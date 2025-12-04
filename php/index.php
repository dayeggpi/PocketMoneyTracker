<?php
/**
 * Pocket Money Tracker
 * A simple PHP app to monitor pocket money saving for kids
 */

// Ensure data directory exists
if (!file_exists('data')) {
    mkdir('data', 0755, true);
}

// Initialize data file if it doesn't exist
$dataFile = 'data/data.json';
if (!file_exists($dataFile)) {
    $initialData = [
        'kids' => [],
        'settings' => [
            'period' => 'monthly',
            'currency' => 'EUR'
        ]
    ];
    file_put_contents($dataFile, json_encode($initialData, JSON_PRETTY_PRINT));
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pocket Money Tracker</title>
    <link rel="stylesheet" href="css/style.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <div class="container">
        <header>
            <h1>💰 Pocket Money Tracker</h1>
            <div class="settings-bar">
                <label for="period">Calculation Period:</label>
                <select id="period">
                    <option value="weekly">Weekly</option>
                    <option value="biweekly">Bi-weekly</option>
                    <option value="monthly" selected>Monthly</option>
                    <option value="quarterly">Quarterly</option>
                </select>
                <span class="currency-display">Currency: EUR</span>
            </div>
        </header>

        <main>
            <!-- Kids Management Section -->
            <section class="section kids-management">
                <h2>👨‍👩‍👧‍👦 Manage Kids</h2>
                <div class="add-kid-form">
                    <input type="text" id="newKidName" placeholder="Enter kid's name">
                    <button onclick="addKid()" class="btn btn-primary">Add Kid</button>
                </div>
                <div id="kidsList" class="kids-list"></div>
            </section>

            <!-- Kid Details Section -->
            <section id="kidDetails" class="section kid-details" style="display: none;">
                <div class="kid-header">
                    <h2 id="selectedKidName"></h2>
                    <button onclick="closeKidDetails()" class="btn btn-secondary">← Back to List</button>
                </div>

                <!-- Bucket Allocation Settings -->
                <div class="allocation-settings">
                    <h3>📊 Default Bucket Allocation</h3>
                    <p class="allocation-hint">This is the default allocation for new entries. You can customize each entry individually.</p>
                    <div class="allocation-inputs">
                        <div class="allocation-item">
                            <label>🛒 Spent %</label>
                            <input type="number" id="spentPercent" min="0" max="100" value="40">
                        </div>
                        <div class="allocation-item">
                            <label>🏦 Saved %</label>
                            <input type="number" id="savedPercent" min="0" max="100" value="40">
                        </div>
                        <div class="allocation-item">
                            <label>🎁 Given %</label>
                            <input type="number" id="givenPercent" min="0" max="100" value="20">
                        </div>
                        <div class="allocation-item">
                            <label>📈 Default Interest %</label>
                            <input type="number" id="interestRate" min="0" max="100" step="0.1" value="0">
                        </div>
                    </div>
                    <div id="allocationError" class="error-message"></div>
                    <button onclick="saveAllocation()" class="btn btn-primary">Save Default Allocation</button>
                </div>

			
				<!-- Add Money Entry -->
				<div class="add-entry">
					<h3>💵 Add Money Entry</h3>
					<div class="entry-form">
						<div class="form-group period-selector">
							<label>Period:</label>
							<div id="periodSelector" class="period-selector-container">
								<!-- Dynamic period selector will be inserted here -->
							</div>
						</div>
						<div class="form-group">
							<label>Amount (EUR):</label>
							<input type="number" id="entryAmount" min="0" step="0.01" placeholder="100">
						</div>
						<div class="form-group">
							<label>Use from Saved (EUR):</label>
							<input type="number" id="entryUsedFromSaved" min="0" step="0.01" value="0" placeholder="0">
							<span class="available-saved-hint">Available: <span id="availableSavedAmount">€0.00</span></span>
						</div>
						<button onclick="addEntry()" class="btn btn-success">Add Entry</button>
					</div>
				</div>	
						

                <!-- Totals Display -->
                <div class="totals-display">
                    <h3>📈 Current Totals</h3>
                    <div class="totals-grid">
                        <div class="total-card spent">
                            <span class="total-label">🛒 Total Spent</span>
                            <span id="totalSpent" class="total-value">0.00 €</span>
                        </div>
                        <div class="total-card saved">
                            <span class="total-label">🏦 Total Saved</span>
                            <span id="totalSaved" class="total-value">0.00 €</span>
                        </div>
                        <div class="total-card given">
                            <span class="total-label">🎁 Total Given</span>
                            <span id="totalGiven" class="total-value">0.00 €</span>
                        </div>
                        <div class="total-card overall">
                            <span class="total-label">💰 Grand Total</span>
                            <span id="grandTotal" class="total-value">0.00 €</span>
                        </div>
                    </div>
                </div>

                <!-- Entries History -->
                <div class="entries-history">
                    <h3>📜 Transaction History</h3>
                    <div class="table-responsive">
						<table id="entriesTable">
							<thead>
								<tr>
									<th>Period</th>
									<th>Amount</th>
									<th>Spent %</th>
									<th>Saved %</th>
									<th>Given %</th>
									<th>Interest %</th>
									<th>Used from Saved</th>
									<th>Running Saved</th>
									<th>Actions</th>
								</tr>
							</thead>
							<tbody id="entriesBody"></tbody>
						</table>
                    </div>
                </div>

                <!-- Chart Section -->
                <div class="chart-section">
                    <h3>📊 Savings Evolution</h3>
                    <div class="chart-container">
                        <canvas id="savingsChart"></canvas>
                    </div>
                </div>
            </section>
        </main>

        <footer>
            <p>Pocket Money Tracker</p>
        </footer>
    </div>

    <!-- Edit Kid Modal -->
    <div id="editKidModal" class="modal">
        <div class="modal-content">
            <h3>Edit Kid's Name</h3>
            <input type="text" id="editKidName" placeholder="Enter new name">
            <input type="hidden" id="editKidId">
            <div class="modal-buttons">
                <button onclick="saveKidName()" class="btn btn-primary">Save</button>
                <button onclick="closeModal('editKidModal')" class="btn btn-secondary">Cancel</button>
            </div>
        </div>
    </div>

    <!-- Confirm Delete Modal -->
    <div id="confirmDeleteModal" class="modal">
        <div class="modal-content">
            <h3>Confirm Delete</h3>
            <p id="deleteConfirmText"></p>
            <input type="hidden" id="deleteKidId">
            <div class="modal-buttons">
                <button onclick="confirmDeleteKid()" class="btn btn-danger">Delete</button>
                <button onclick="closeModal('confirmDeleteModal')" class="btn btn-secondary">Cancel</button>
            </div>
        </div>
    </div>

    <!-- Edit Entry Modal -->
    <div id="editEntryModal" class="modal">
        <div class="modal-content modal-content-lg">
            <h3>📝 Edit Entry</h3>
            <input type="hidden" id="editEntryId">
            <input type="hidden" id="editEntryOriginalPeriod">
            
            <!-- Period Section -->
            <div class="edit-entry-section">
                <h4>📅 Period</h4>
                <div class="edit-period-selector">
                    <div class="period-type-selector">
                        <label>Type:</label>
                        <select id="editPeriodType" onchange="updateEditPeriodSelector()">
                            <option value="weekly">Weekly</option>
                            <option value="biweekly">Bi-weekly</option>
                            <option value="monthly">Monthly</option>
                            <option value="quarterly">Quarterly</option>
                        </select>
                    </div>
                    <div id="editPeriodSelectors" class="edit-period-selectors">
                        <!-- Dynamic period selectors will be inserted here -->
                    </div>
                    <div class="period-display-edit" id="editPeriodDisplay"></div>
                </div>
            </div>
            
					
			<!-- Amount Section -->
			<div class="edit-entry-section">
				<h4>💵 Amount</h4>
				<div class="form-group">
					<label>Amount (EUR):</label>
					<input type="number" id="editEntryAmount" min="0.01" step="0.01" class="amount-input">
				</div>
				<div class="form-group">
					<label>Use from Saved (EUR):</label>
					<input type="number" id="editUsedFromSaved" min="0" step="0.01" value="0">
					<span class="available-saved-hint">Available at this point: <span id="editAvailableSavedAmount">€0.00</span></span>
				</div>
			</div>
			
            <!-- Allocation Section -->
            <div class="edit-entry-section">
                <h4>📊 Allocation</h4>
                <div class="allocation-inputs compact">
                    <div class="allocation-item">
                        <label>🛒 Spent %</label>
                        <input type="number" id="editSpentPercent" min="0" max="100" step="0.1">
                        <span class="calculated-amount" id="editSpentAmount"></span>
                    </div>
                    <div class="allocation-item">
                        <label>🏦 Saved %</label>
                        <input type="number" id="editSavedPercent" min="0" max="100" step="0.1">
                        <span class="calculated-amount" id="editSavedAmount"></span>
                    </div>
                    <div class="allocation-item">
                        <label>🎁 Given %</label>
                        <input type="number" id="editGivenPercent" min="0" max="100" step="0.1">
                        <span class="calculated-amount" id="editGivenAmount"></span>
                    </div>
                    <div class="allocation-item">
                        <label>📈 Interest %</label>
                        <input type="number" id="editInterestRate" min="0" max="100" step="0.1">
                        <span class="calculated-amount">&nbsp;</span>
                    </div>
                </div>
                <div id="editAllocationError" class="error-message"></div>
                <div class="allocation-total">
                    <span>Total: </span>
                    <span id="editAllocationTotal">100%</span>
                </div>
            </div>
            
            <!-- Summary Section -->
            <div class="edit-entry-summary">
                <h4>📋 Summary</h4>
                <div class="summary-grid">
                    <div class="summary-item spent">
                        <span class="summary-label">Spent</span>
                        <span class="summary-value" id="summarySpent">€0.00</span>
                    </div>
                    <div class="summary-item saved">
                        <span class="summary-label">Saved</span>
                        <span class="summary-value" id="summarySaved">€0.00</span>
                    </div>
                    <div class="summary-item given">
                        <span class="summary-label">Given</span>
                        <span class="summary-value" id="summaryGiven">€0.00</span>
                    </div>
                </div>
            </div>
            
            <div class="modal-buttons">
                <button onclick="saveEntryChanges()" class="btn btn-primary">Save Changes</button>
                <button onclick="closeModal('editEntryModal')" class="btn btn-secondary">Cancel</button>
            </div>
        </div>
    </div>

    <script src="js/app.js"></script>
</body>
</html>