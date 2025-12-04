<?php
/**
 * API Handler for Pocket Money Tracker
 * Handles all CRUD operations with JSON file storage
 */

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, PUT, DELETE');
header('Access-Control-Allow-Headers: Content-Type');

$dataFile = 'data/data.json';

// Load data from JSON file
function loadData() {
    global $dataFile;
    if (!file_exists($dataFile)) {
        return ['kids' => [], 'settings' => ['period' => 'monthly', 'currency' => 'EUR']];
    }
    $content = file_get_contents($dataFile);
    return json_decode($content, true) ?: ['kids' => [], 'settings' => ['period' => 'monthly', 'currency' => 'EUR']];
}

// Save data to JSON file
function saveData($data) {
    global $dataFile;
    if (!file_exists('data')) {
        mkdir('data', 0755, true);
    }
    file_put_contents($dataFile, json_encode($data, JSON_PRETTY_PRINT));
}

// Generate unique ID
function generateId() {
    return uniqid('kid_', true);
}

// Calculate totals with interest for a kid
// Calculate totals with interest for a kid
// Calculate totals with interest for a kid
function calculateTotals($kid) {
    $totalSpent = 0;
    $totalSaved = 0;
    $totalGiven = 0;
    $totalInterest = 0;
    $totalUsedFromSaved = 0;
    
    $entries = $kid['entries'] ?? [];
    
    // Sort entries by period
    usort($entries, function($a, $b) {
        return strcmp($a['period'], $b['period']);
    });
    
    $runningSaved = 0;
    
    foreach ($entries as &$entry) {
        // Apply interest to running saved before adding new amount
        $interestRate = $entry['interestRate'] ?? 0;
        $interestAmount = $runningSaved * ($interestRate / 100);
        $totalInterest += $interestAmount;
        $runningSaved += $interestAmount;
        
        // Add new allocations
        $totalSpent += $entry['spent'];
        $runningSaved += $entry['saved'];
        $totalGiven += $entry['given'];
        
        // Subtract used from saved
        $usedFromSaved = $entry['usedFromSaved'] ?? 0;
        $runningSaved -= $usedFromSaved;
        $totalUsedFromSaved += $usedFromSaved;
        
        $entry['interestEarned'] = $interestAmount;
        $entry['runningSaved'] = $runningSaved;
        $entry['availableSavedBefore'] = $runningSaved + $usedFromSaved - $entry['saved'];
    }
    
    $totalSaved = $runningSaved;
    
    // Total spent includes both allocated spent AND used from saved
    $totalSpentWithUsed = $totalSpent + $totalUsedFromSaved;
    
    return [
        'totalSpent' => round($totalSpentWithUsed, 2),
        'totalAllocatedSpent' => round($totalSpent, 2),
        'totalSaved' => round($totalSaved, 2),
        'totalGiven' => round($totalGiven, 2),
        'totalInterest' => round($totalInterest, 2),
        'totalUsedFromSaved' => round($totalUsedFromSaved, 2),
        'grandTotal' => round($totalSpentWithUsed + $totalSaved + $totalGiven, 2),
        'currentSaved' => round($runningSaved, 2),
        'entries' => $entries
    ];
}


// Get request method and action
$method = $_SERVER['REQUEST_METHOD'];
$action = $_GET['action'] ?? '';

try {
    switch ($method) {
        case 'GET':
            handleGet($action);
            break;
        case 'POST':
            handlePost($action);
            break;
        case 'PUT':
            handlePut($action);
            break;
        case 'DELETE':
            handleDelete($action);
            break;
        default:
            http_response_code(405);
            echo json_encode(['error' => 'Method not allowed']);
    }
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(['error' => $e->getMessage()]);
}

function handleGet($action) {
    $data = loadData();
    
    switch ($action) {
        case 'getKids':
            $kids = [];
            foreach ($data['kids'] as $kid) {
                $totals = calculateTotals($kid);
                $kids[] = [
                    'id' => $kid['id'],
                    'name' => $kid['name'],
                    'allocation' => $kid['allocation'],
                    'interestRate' => $kid['interestRate'] ?? 0,
                    'totals' => $totals
                ];
            }
            echo json_encode(['success' => true, 'kids' => $kids]);
            break;
            
        case 'getKid':
            $kidId = $_GET['id'] ?? '';
            $kid = findKid($data, $kidId);
            if ($kid) {
                $totals = calculateTotals($kid);
                $kid['totals'] = $totals;
                $kid['entries'] = $totals['entries'];
                echo json_encode(['success' => true, 'kid' => $kid]);
            } else {
                http_response_code(404);
                echo json_encode(['error' => 'Kid not found']);
            }
            break;
            
        case 'getSettings':
            echo json_encode(['success' => true, 'settings' => $data['settings']]);
            break;
            
        default:
            echo json_encode(['success' => true, 'data' => $data]);
    }
}

function handlePost($action) {
    $input = json_decode(file_get_contents('php://input'), true);
    $data = loadData();
    
    switch ($action) {
        case 'addKid':
            $name = trim($input['name'] ?? '');
            if (empty($name)) {
                http_response_code(400);
                echo json_encode(['error' => 'Name is required']);
                return;
            }
            
            $newKid = [
                'id' => generateId(),
                'name' => $name,
                'allocation' => [
                    'spent' => 40,
                    'saved' => 40,
                    'given' => 20
                ],
                'interestRate' => 0,
                'entries' => []
            ];
            
            $data['kids'][] = $newKid;
            saveData($data);
            echo json_encode(['success' => true, 'kid' => $newKid]);
            break;
            
		case 'addEntry':
			$kidId = $input['kidId'] ?? '';
			$period = $input['period'] ?? '';
			$periodType = $input['periodType'] ?? 'monthly';
			$amount = floatval($input['amount'] ?? 0);
			$interestRate = floatval($input['interestRate'] ?? 0);
			$usedFromSaved = floatval($input['usedFromSaved'] ?? 0);
			$spentPercent = isset($input['spentPercent']) ? floatval($input['spentPercent']) : null;
			$savedPercent = isset($input['savedPercent']) ? floatval($input['savedPercent']) : null;
			$givenPercent = isset($input['givenPercent']) ? floatval($input['givenPercent']) : null;
			
			if (empty($kidId) || empty($period) || $amount <= 0) {
				http_response_code(400);
				echo json_encode(['error' => 'Kid ID, period, and positive amount are required']);
				return;
			}
			
			$kidIndex = findKidIndex($data, $kidId);
			if ($kidIndex === -1) {
				http_response_code(404);
				echo json_encode(['error' => 'Kid not found']);
				return;
			}
			
			$kid = &$data['kids'][$kidIndex];
			
			// Calculate current saved to validate usedFromSaved
			$currentTotals = calculateTotals($kid);
			$availableSaved = $currentTotals['currentSaved'] ?? 0;
			
			// Apply interest for this period to get accurate available amount
			$interestOnCurrent = $availableSaved * ($interestRate / 100);
			$availableSaved += $interestOnCurrent;
			
			if ($usedFromSaved < 0) {
				http_response_code(400);
				echo json_encode(['error' => 'Used from saved cannot be negative']);
				return;
			}
			
			if ($usedFromSaved > $availableSaved) {
				http_response_code(400);
				echo json_encode(['error' => 'Cannot use more than available in saved bucket (€' . number_format($availableSaved, 2) . ' available)']);
				return;
			}
			
			// Use custom allocation if provided, otherwise use default
			if ($spentPercent !== null && $savedPercent !== null && $givenPercent !== null) {
				$allocation = [
					'spent' => $spentPercent,
					'saved' => $savedPercent,
					'given' => $givenPercent
				];
			} else {
				$allocation = $kid['allocation'];
			}
			
			// Check if entry for this period already exists
			foreach ($kid['entries'] as $entry) {
				if ($entry['period'] === $period) {
					http_response_code(400);
					echo json_encode(['error' => 'Entry for this period already exists']);
					return;
				}
			}
			
			$newEntry = [
				'id' => uniqid('entry_', true),
				'period' => $period,
				'periodType' => $periodType,
				'amount' => $amount,
				'spentPercent' => $allocation['spent'],
				'savedPercent' => $allocation['saved'],
				'givenPercent' => $allocation['given'],
				'spent' => round($amount * $allocation['spent'] / 100, 2),
				'saved' => round($amount * $allocation['saved'] / 100, 2),
				'given' => round($amount * $allocation['given'] / 100, 2),
				'interestRate' => $interestRate,
				'usedFromSaved' => $usedFromSaved,
				'createdAt' => date('Y-m-d H:i:s')
			];
			
			$kid['entries'][] = $newEntry;
			saveData($data);
			
			$totals = calculateTotals($kid);
			echo json_encode(['success' => true, 'entry' => $newEntry, 'totals' => $totals]);
			break;
            
        default:
            http_response_code(400);
            echo json_encode(['error' => 'Invalid action']);
    }
}

function handlePut($action) {
    $input = json_decode(file_get_contents('php://input'), true);
    $data = loadData();
    
    switch ($action) {
        case 'updateKid':
            $kidId = $input['id'] ?? '';
            $name = trim($input['name'] ?? '');
            
            if (empty($kidId) || empty($name)) {
                http_response_code(400);
                echo json_encode(['error' => 'Kid ID and name are required']);
                return;
            }
            
            $kidIndex = findKidIndex($data, $kidId);
            if ($kidIndex === -1) {
                http_response_code(404);
                echo json_encode(['error' => 'Kid not found']);
                return;
            }
            
            $data['kids'][$kidIndex]['name'] = $name;
            saveData($data);
            echo json_encode(['success' => true, 'kid' => $data['kids'][$kidIndex]]);
            break;
            
        case 'updateAllocation':
            $kidId = $input['kidId'] ?? '';
            $spent = floatval($input['spent'] ?? 0);
            $saved = floatval($input['saved'] ?? 0);
            $given = floatval($input['given'] ?? 0);
            $interestRate = floatval($input['interestRate'] ?? 0);
            
            if (abs($spent + $saved + $given - 100) > 0.01) {
                http_response_code(400);
                echo json_encode(['error' => 'Allocation must total 100%']);
                return;
            }
            
            $kidIndex = findKidIndex($data, $kidId);
            if ($kidIndex === -1) {
                http_response_code(404);
                echo json_encode(['error' => 'Kid not found']);
                return;
            }
            
            $data['kids'][$kidIndex]['allocation'] = [
                'spent' => $spent,
                'saved' => $saved,
                'given' => $given
            ];
            $data['kids'][$kidIndex]['interestRate'] = $interestRate;
            
            saveData($data);
            echo json_encode(['success' => true, 'allocation' => $data['kids'][$kidIndex]['allocation']]);
            break;
            
        case 'updateSettings':
            $period = $input['period'] ?? 'monthly';
            $data['settings']['period'] = $period;
            saveData($data);
            echo json_encode(['success' => true, 'settings' => $data['settings']]);
            break;
            
        case 'updateEntry':
			$kidId = $input['kidId'] ?? '';
			$entryId = $input['entryId'] ?? '';
			$amount = isset($input['amount']) ? floatval($input['amount']) : null;
			$period = isset($input['period']) ? trim($input['period']) : null;
			$periodType = isset($input['periodType']) ? trim($input['periodType']) : null;
			$interestRate = isset($input['interestRate']) ? floatval($input['interestRate']) : null;
			$usedFromSaved = isset($input['usedFromSaved']) ? floatval($input['usedFromSaved']) : null;
			$spentPercent = isset($input['spentPercent']) ? floatval($input['spentPercent']) : null;
			$savedPercent = isset($input['savedPercent']) ? floatval($input['savedPercent']) : null;
			$givenPercent = isset($input['givenPercent']) ? floatval($input['givenPercent']) : null;
			
			$kidIndex = findKidIndex($data, $kidId);
			if ($kidIndex === -1) {
				http_response_code(404);
				echo json_encode(['error' => 'Kid not found']);
				return;
			}
			
			// Check if new period already exists (if period is being changed)
			if ($period !== null) {
				foreach ($data['kids'][$kidIndex]['entries'] as $entry) {
					if ($entry['period'] === $period && $entry['id'] !== $entryId) {
						http_response_code(400);
						echo json_encode(['error' => 'An entry for this period already exists']);
						return;
					}
				}
			}
			
			$entryFound = false;
			$entryIndex = -1;
			foreach ($data['kids'][$kidIndex]['entries'] as $idx => &$entry) {
				if ($entry['id'] === $entryId) {
					$entryIndex = $idx;
					$entryFound = true;
					break;
				}
			}
			
			if (!$entryFound) {
				http_response_code(404);
				echo json_encode(['error' => 'Entry not found']);
				return;
			}
			
			// Validate usedFromSaved if it's being updated
			if ($usedFromSaved !== null) {
				if ($usedFromSaved < 0) {
					http_response_code(400);
					echo json_encode(['error' => 'Used from saved cannot be negative']);
					return;
				}
				
				// Calculate available saved at this entry's position
				// Temporarily set usedFromSaved to 0 to calculate available
				$originalUsedFromSaved = $data['kids'][$kidIndex]['entries'][$entryIndex]['usedFromSaved'] ?? 0;
				$data['kids'][$kidIndex]['entries'][$entryIndex]['usedFromSaved'] = 0;
				
				$tempTotals = calculateTotals($data['kids'][$kidIndex]);
				$tempEntries = $tempTotals['entries'];
				
				// Find the entry in calculated totals to get availableSavedBefore
				$availableSaved = 0;
				foreach ($tempEntries as $tempEntry) {
					if ($tempEntry['id'] === $entryId) {
						// Available = running saved at this point (which includes this entry's saved contribution)
						$availableSaved = $tempEntry['runningSaved'];
						break;
					}
				}
				
				// Restore original value for now
				$data['kids'][$kidIndex]['entries'][$entryIndex]['usedFromSaved'] = $originalUsedFromSaved;
				
				if ($usedFromSaved > $availableSaved) {
					http_response_code(400);
					echo json_encode(['error' => 'Cannot use more than available in saved bucket (€' . number_format($availableSaved, 2) . ' available at this point)']);
					return;
				}
			}
			
			// Now apply updates
			$entry = &$data['kids'][$kidIndex]['entries'][$entryIndex];
			
			// Update period if provided
			if ($period !== null && !empty($period)) {
				$entry['period'] = $period;
			}
			
			// Update period type if provided
			if ($periodType !== null && !empty($periodType)) {
				$entry['periodType'] = $periodType;
			}
			
			// Update amount if provided
			if ($amount !== null && $amount > 0) {
				$entry['amount'] = $amount;
			}
			
			// Update interest rate if provided
			if ($interestRate !== null) {
				$entry['interestRate'] = $interestRate;
			}
			
			// Update usedFromSaved if provided
			if ($usedFromSaved !== null) {
				$entry['usedFromSaved'] = $usedFromSaved;
			}
			
			// Update allocation if all three percentages are provided
			if ($spentPercent !== null && $savedPercent !== null && $givenPercent !== null) {
				// Validate total is 100%
				if (abs($spentPercent + $savedPercent + $givenPercent - 100) > 0.01) {
					http_response_code(400);
					echo json_encode(['error' => 'Allocation must total 100%']);
					return;
				}
				
				$entry['spentPercent'] = $spentPercent;
				$entry['savedPercent'] = $savedPercent;
				$entry['givenPercent'] = $givenPercent;
			}
			
			// Recalculate amounts based on current amount and percentages
			$currentAmount = $entry['amount'];
			$entry['spent'] = round($currentAmount * $entry['spentPercent'] / 100, 2);
			$entry['saved'] = round($currentAmount * $entry['savedPercent'] / 100, 2);
			$entry['given'] = round($currentAmount * $entry['givenPercent'] / 100, 2);
			
			$entry['updatedAt'] = date('Y-m-d H:i:s');
			
			saveData($data);
			$totals = calculateTotals($data['kids'][$kidIndex]);
			echo json_encode(['success' => true, 'totals' => $totals]);
			break;
            
        default:
            http_response_code(400);
            echo json_encode(['error' => 'Invalid action']);
    }
}

function handleDelete($action) {
    $data = loadData();
    
    switch ($action) {
        case 'deleteKid':
            $kidId = $_GET['id'] ?? '';
            
            $kidIndex = findKidIndex($data, $kidId);
            if ($kidIndex === -1) {
                http_response_code(404);
                echo json_encode(['error' => 'Kid not found']);
                return;
            }
            
            array_splice($data['kids'], $kidIndex, 1);
            saveData($data);
            echo json_encode(['success' => true]);
            break;
            
        case 'deleteEntry':
            $kidId = $_GET['kidId'] ?? '';
            $entryId = $_GET['entryId'] ?? '';
            
            $kidIndex = findKidIndex($data, $kidId);
            if ($kidIndex === -1) {
                http_response_code(404);
                echo json_encode(['error' => 'Kid not found']);
                return;
            }
            
            $entries = &$data['kids'][$kidIndex]['entries'];
            $entryIndex = -1;
            foreach ($entries as $i => $entry) {
                if ($entry['id'] === $entryId) {
                    $entryIndex = $i;
                    break;
                }
            }
            
            if ($entryIndex === -1) {
                http_response_code(404);
                echo json_encode(['error' => 'Entry not found']);
                return;
            }
            
            array_splice($entries, $entryIndex, 1);
            saveData($data);
            
            $totals = calculateTotals($data['kids'][$kidIndex]);
            echo json_encode(['success' => true, 'totals' => $totals]);
            break;
            
        default:
            http_response_code(400);
            echo json_encode(['error' => 'Invalid action']);
    }
}

function findKid($data, $kidId) {
    foreach ($data['kids'] as $kid) {
        if ($kid['id'] === $kidId) {
            return $kid;
        }
    }
    return null;
}

function findKidIndex($data, $kidId) {
    foreach ($data['kids'] as $i => $kid) {
        if ($kid['id'] === $kidId) {
            return $i;
        }
    }
    return -1;
}
?>