/**
 * Pocket Money Tracker - Frontend JavaScript
 */

// Global state
let currentKid = null;
let chart = null;
let currentPeriodType = 'monthly';
let selectedPeriod = null;
let editingEntryData = null;
let editPeriodState = null;

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    loadKids();
    loadSettings();
    
    // Add event listeners
    document.getElementById('period').addEventListener('change', (e) => {
        currentPeriodType = e.target.value;
        updateSettings({ period: e.target.value });
        initializePeriodSelector();
    });
    
    // Allocation validation for default settings
    ['spentPercent', 'savedPercent', 'givenPercent'].forEach(id => {
        document.getElementById(id).addEventListener('input', validateAllocation);
    });
    
	// Edit entry validation - allocation, amount, and usedFromSaved
	['editSpentPercent', 'editSavedPercent', 'editGivenPercent', 'editEntryAmount', 'editUsedFromSaved'].forEach(id => {
		document.getElementById(id).addEventListener('input', validateAndUpdateEditEntry);
	});

});

// API Helper Functions
async function apiCall(url, method = 'GET', data = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json'
        }
    };
    
    if (data && (method === 'POST' || method === 'PUT')) {
        options.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(url, options);
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.error || 'An error occurred');
        }
        
        return result;
    } catch (error) {
        showToast(error.message, 'error');
        throw error;
    }
}

// Load all kids
async function loadKids() {
    try {
        const result = await apiCall('api.php?action=getKids');
        renderKidsList(result.kids);
    } catch (error) {
        console.error('Failed to load kids:', error);
    }
}

// Load settings
async function loadSettings() {
    try {
        const result = await apiCall('api.php?action=getSettings');
        currentPeriodType = result.settings.period;
        document.getElementById('period').value = result.settings.period;
        initializePeriodSelector();
    } catch (error) {
        console.error('Failed to load settings:', error);
    }
}

// Update settings
async function updateSettings(settings) {
    try {
        await apiCall('api.php?action=updateSettings', 'PUT', settings);
        showToast('Settings updated', 'success');
    } catch (error) {
        console.error('Failed to update settings:', error);
    }
}

// ============================================
// PERIOD SELECTOR FUNCTIONS (for Add Entry)
// ============================================

function initializePeriodSelector() {
    const container = document.getElementById('periodSelector');
    if (!container) return;
    
    const now = new Date();
    selectedPeriod = getCurrentPeriod(now);
    
    renderPeriodSelector(container, currentPeriodType, selectedPeriod, false);
}

function getCurrentPeriod(date) {
    const year = date.getFullYear();
    const month = date.getMonth();
    
    switch (currentPeriodType) {
        case 'weekly':
            const weekNum = getWeekNumber(date);
            return { year, week: weekNum, type: 'weekly' };
        case 'biweekly':
            const biweekNum = Math.ceil(getWeekNumber(date) / 2);
            return { year, biweek: biweekNum, type: 'biweekly' };
        case 'monthly':
            return { year, month: month + 1, type: 'monthly' };
        case 'quarterly':
            const quarter = Math.ceil((month + 1) / 3);
            return { year, quarter, type: 'quarterly' };
        default:
            return { year, month: month + 1, type: 'monthly' };
    }
}

function getWeekNumber(date) {
    const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
    const dayNum = d.getUTCDay() || 7;
    d.setUTCDate(d.getUTCDate() + 4 - dayNum);
    const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
    return Math.ceil((((d - yearStart) / 86400000) + 1) / 7);
}

function getWeeksInYear(year) {
    const d = new Date(year, 11, 31);
    const week = getWeekNumber(d);
    return week === 1 ? 52 : week;
}

function renderPeriodSelector(container, periodType, period, isEdit = false) {
    const prefix = isEdit ? 'edit' : '';
    const year = period?.year || new Date().getFullYear();
    
    let html = '';
    
    switch (periodType) {
        case 'weekly':
            html = createWeeklySelectorHTML(year, period?.week || 1, prefix);
            break;
        case 'biweekly':
            html = createBiweeklySelectorHTML(year, period?.biweek || 1, prefix);
            break;
        case 'monthly':
            html = createMonthlySelectorHTML(year, period?.month || 1, prefix);
            break;
        case 'quarterly':
            html = createQuarterlySelectorHTML(year, period?.quarter || 1, prefix);
            break;
    }
    
    container.innerHTML = html;
    
    // Update display
    if (isEdit) {
        updateEditPeriodDisplay();
    } else {
        updatePeriodDisplay();
    }
}

function createWeeklySelectorHTML(year, selectedWeek, prefix = '') {
    const weeksInYear = getWeeksInYear(year);
    let weekOptions = '';
    
    for (let w = 1; w <= weeksInYear; w++) {
        const weekStart = getDateOfWeek(w, year);
        const weekEnd = new Date(weekStart);
        weekEnd.setDate(weekEnd.getDate() + 6);
        const label = `Week ${w} (${formatShortDate(weekStart)} - ${formatShortDate(weekEnd)})`;
        weekOptions += `<option value="${w}" ${w === selectedWeek ? 'selected' : ''}>${label}</option>`;
    }
    
    const yearOptions = generateYearOptions(year);
    const onchangeFunc = prefix ? 'onYearChangeEdit' : 'onYearChange';
    const updateFunc = prefix ? 'updateEditSelectedPeriod' : 'updateSelectedPeriod';
    const navFunc = prefix ? 'navigateEditPeriod' : 'navigatePeriod';
    
    return `
        <div class="period-select-group">
            ${!prefix ? `
            <div class="period-nav-buttons">
                <button type="button" class="period-nav-btn" onclick="${navFunc}(-1)" title="Previous">◀</button>
            </div>
            ` : ''}
            <select id="${prefix}periodWeek" onchange="${updateFunc}()">
                ${weekOptions}
            </select>
            <select id="${prefix}periodYear" onchange="${onchangeFunc}()">
                ${yearOptions}
            </select>
            ${!prefix ? `
            <div class="period-nav-buttons">
                <button type="button" class="period-nav-btn" onclick="${navFunc}(1)" title="Next">▶</button>
            </div>
            ` : ''}
        </div>
        ${!prefix ? `<div class="period-display" id="periodDisplay"></div>` : ''}
    `;
}

function createBiweeklySelectorHTML(year, selectedBiweek, prefix = '') {
    const weeksInYear = getWeeksInYear(year);
    const biweeksInYear = Math.ceil(weeksInYear / 2);
    let biweekOptions = '';
    
    for (let bw = 1; bw <= biweeksInYear; bw++) {
        const startWeek = (bw - 1) * 2 + 1;
        const endWeek = Math.min(startWeek + 1, weeksInYear);
        const startDate = getDateOfWeek(startWeek, year);
        const endDate = getDateOfWeek(endWeek, year);
        endDate.setDate(endDate.getDate() + 6);
        const label = `Period ${bw} (${formatShortDate(startDate)} - ${formatShortDate(endDate)})`;
        biweekOptions += `<option value="${bw}" ${bw === selectedBiweek ? 'selected' : ''}>${label}</option>`;
    }
    
    const yearOptions = generateYearOptions(year);
    const onchangeFunc = prefix ? 'onYearChangeEdit' : 'onYearChange';
    const updateFunc = prefix ? 'updateEditSelectedPeriod' : 'updateSelectedPeriod';
    const navFunc = prefix ? 'navigateEditPeriod' : 'navigatePeriod';
    
    return `
        <div class="period-select-group">
            ${!prefix ? `
            <div class="period-nav-buttons">
                <button type="button" class="period-nav-btn" onclick="${navFunc}(-1)" title="Previous">◀</button>
            </div>
            ` : ''}
            <select id="${prefix}periodBiweek" onchange="${updateFunc}()">
                ${biweekOptions}
            </select>
            <select id="${prefix}periodYear" onchange="${onchangeFunc}()">
                ${yearOptions}
            </select>
            ${!prefix ? `
            <div class="period-nav-buttons">
                <button type="button" class="period-nav-btn" onclick="${navFunc}(1)" title="Next">▶</button>
            </div>
            ` : ''}
        </div>
        ${!prefix ? `<div class="period-display" id="periodDisplay"></div>` : ''}
    `;
}

function createMonthlySelectorHTML(year, selectedMonth, prefix = '') {
    const months = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    ];
    
    let monthOptions = '';
    months.forEach((m, i) => {
        monthOptions += `<option value="${i + 1}" ${(i + 1) === selectedMonth ? 'selected' : ''}>${m}</option>`;
    });
    
    const yearOptions = generateYearOptions(year);
    const updateFunc = prefix ? 'updateEditSelectedPeriod' : 'updateSelectedPeriod';
    const navFunc = prefix ? 'navigateEditPeriod' : 'navigatePeriod';
    
    return `
        <div class="period-select-group">
            ${!prefix ? `
            <div class="period-nav-buttons">
                <button type="button" class="period-nav-btn" onclick="${navFunc}(-1)" title="Previous">◀</button>
            </div>
            ` : ''}
            <select id="${prefix}periodMonth" onchange="${updateFunc}()">
                ${monthOptions}
            </select>
            <select id="${prefix}periodYear" onchange="${updateFunc}()">
                ${yearOptions}
            </select>
            ${!prefix ? `
            <div class="period-nav-buttons">
                <button type="button" class="period-nav-btn" onclick="${navFunc}(1)" title="Next">▶</button>
            </div>
            ` : ''}
        </div>
        ${!prefix ? `<div class="period-display" id="periodDisplay"></div>` : ''}
    `;
}

function createQuarterlySelectorHTML(year, selectedQuarter, prefix = '') {
    const quarters = [
        { value: 1, label: 'Q1 (Jan - Mar)' },
        { value: 2, label: 'Q2 (Apr - Jun)' },
        { value: 3, label: 'Q3 (Jul - Sep)' },
        { value: 4, label: 'Q4 (Oct - Dec)' }
    ];
    
    let quarterOptions = '';
    quarters.forEach(q => {
        quarterOptions += `<option value="${q.value}" ${q.value === selectedQuarter ? 'selected' : ''}>${q.label}</option>`;
    });
    
    const yearOptions = generateYearOptions(year);
    const updateFunc = prefix ? 'updateEditSelectedPeriod' : 'updateSelectedPeriod';
    const navFunc = prefix ? 'navigateEditPeriod' : 'navigatePeriod';
    
    return `
        <div class="period-select-group">
            ${!prefix ? `
            <div class="period-nav-buttons">
                <button type="button" class="period-nav-btn" onclick="${navFunc}(-1)" title="Previous">◀</button>
            </div>
            ` : ''}
            <select id="${prefix}periodQuarter" onchange="${updateFunc}()">
                ${quarterOptions}
            </select>
            <select id="${prefix}periodYear" onchange="${updateFunc}()">
                ${yearOptions}
            </select>
            ${!prefix ? `
            <div class="period-nav-buttons">
                <button type="button" class="period-nav-btn" onclick="${navFunc}(1)" title="Next">▶</button>
            </div>
            ` : ''}
        </div>
        ${!prefix ? `<div class="period-display" id="periodDisplay"></div>` : ''}
    `;
}

function generateYearOptions(selectedYear) {
    const currentYear = new Date().getFullYear();
    let options = '';
    for (let y = currentYear - 5; y <= currentYear + 2; y++) {
        options += `<option value="${y}" ${y === selectedYear ? 'selected' : ''}>${y}</option>`;
    }
    return options;
}

function getDateOfWeek(week, year) {
    const simple = new Date(year, 0, 1 + (week - 1) * 7);
    const dow = simple.getDay();
    const weekStart = new Date(simple);
    if (dow <= 4) {
        weekStart.setDate(simple.getDate() - simple.getDay() + 1);
    } else {
        weekStart.setDate(simple.getDate() + 8 - simple.getDay());
    }
    return weekStart;
}

function formatShortDate(date) {
    return date.toLocaleDateString('en-GB', { day: '2-digit', month: 'short' });
}

// When year changes, we need to regenerate the period options
function onYearChange() {
    const year = parseInt(document.getElementById('periodYear')?.value) || new Date().getFullYear();
    const container = document.getElementById('periodSelector');
    
    // Preserve current selection if possible
    let currentValue = 1;
    switch (currentPeriodType) {
        case 'weekly':
            currentValue = parseInt(document.getElementById('periodWeek')?.value) || 1;
            break;
        case 'biweekly':
            currentValue = parseInt(document.getElementById('periodBiweek')?.value) || 1;
            break;
        case 'monthly':
            currentValue = parseInt(document.getElementById('periodMonth')?.value) || 1;
            break;
        case 'quarterly':
            currentValue = parseInt(document.getElementById('periodQuarter')?.value) || 1;
            break;
    }
    
    // Adjust if out of range for new year
    if (currentPeriodType === 'weekly') {
        const weeksInYear = getWeeksInYear(year);
        currentValue = Math.min(currentValue, weeksInYear);
    } else if (currentPeriodType === 'biweekly') {
        const biweeksInYear = Math.ceil(getWeeksInYear(year) / 2);
        currentValue = Math.min(currentValue, biweeksInYear);
    }
    
    selectedPeriod = {
        year,
        type: currentPeriodType,
        ...(currentPeriodType === 'weekly' && { week: currentValue }),
        ...(currentPeriodType === 'biweekly' && { biweek: currentValue }),
        ...(currentPeriodType === 'monthly' && { month: currentValue }),
        ...(currentPeriodType === 'quarterly' && { quarter: currentValue })
    };
    
    renderPeriodSelector(container, currentPeriodType, selectedPeriod, false);
}

function updateSelectedPeriod() {
    const yearEl = document.getElementById('periodYear');
    const year = parseInt(yearEl?.value) || new Date().getFullYear();
    
    switch (currentPeriodType) {
        case 'weekly':
            const week = parseInt(document.getElementById('periodWeek')?.value) || 1;
            selectedPeriod = { year, week, type: 'weekly' };
            break;
        case 'biweekly':
            const biweek = parseInt(document.getElementById('periodBiweek')?.value) || 1;
            selectedPeriod = { year, biweek, type: 'biweekly' };
            break;
        case 'monthly':
            const month = parseInt(document.getElementById('periodMonth')?.value) || 1;
            selectedPeriod = { year, month, type: 'monthly' };
            break;
        case 'quarterly':
            const quarter = parseInt(document.getElementById('periodQuarter')?.value) || 1;
            selectedPeriod = { year, quarter, type: 'quarterly' };
            break;
    }
    
    updatePeriodDisplay();
}

function updatePeriodDisplay() {
    const display = document.getElementById('periodDisplay');
    if (display && selectedPeriod) {
        display.textContent = formatPeriodDisplayText(selectedPeriod);
    }
}

function navigatePeriod(direction) {
    if (!selectedPeriod) return;
    
    const year = selectedPeriod.year;
    
    switch (currentPeriodType) {
        case 'weekly':
            const weeksInYear = getWeeksInYear(year);
            selectedPeriod.week += direction;
            if (selectedPeriod.week < 1) {
                selectedPeriod.year--;
                selectedPeriod.week = getWeeksInYear(selectedPeriod.year);
            } else if (selectedPeriod.week > weeksInYear) {
                selectedPeriod.year++;
                selectedPeriod.week = 1;
            }
            break;
        case 'biweekly':
            const biweeksInYear = Math.ceil(getWeeksInYear(year) / 2);
            selectedPeriod.biweek += direction;
            if (selectedPeriod.biweek < 1) {
                selectedPeriod.year--;
                selectedPeriod.biweek = Math.ceil(getWeeksInYear(selectedPeriod.year) / 2);
            } else if (selectedPeriod.biweek > biweeksInYear) {
                selectedPeriod.year++;
                selectedPeriod.biweek = 1;
            }
            break;
        case 'monthly':
            selectedPeriod.month += direction;
            if (selectedPeriod.month < 1) {
                selectedPeriod.month = 12;
                selectedPeriod.year--;
            } else if (selectedPeriod.month > 12) {
                selectedPeriod.month = 1;
                selectedPeriod.year++;
            }
            break;
        case 'quarterly':
            selectedPeriod.quarter += direction;
            if (selectedPeriod.quarter < 1) {
                selectedPeriod.quarter = 4;
                selectedPeriod.year--;
            } else if (selectedPeriod.quarter > 4) {
                selectedPeriod.quarter = 1;
                selectedPeriod.year++;
            }
            break;
    }
    
    const container = document.getElementById('periodSelector');
    renderPeriodSelector(container, currentPeriodType, selectedPeriod, false);
}

function formatPeriodDisplayText(period) {
    if (!period) return '';
    
    switch (period.type) {
        case 'weekly':
            return `Week ${period.week}, ${period.year}`;
        case 'biweekly':
            return `Period ${period.biweek}, ${period.year}`;
        case 'monthly':
            const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
            return `${monthNames[period.month - 1]} ${period.year}`;
        case 'quarterly':
            return `Q${period.quarter} ${period.year}`;
        default:
            return '';
    }
}

function getPeriodKey() {
    if (!selectedPeriod) return '';
    return periodToKey(selectedPeriod);
}

function periodToKey(period) {
    switch (period.type) {
        case 'weekly':
            return `${period.year}-W${String(period.week).padStart(2, '0')}`;
        case 'biweekly':
            return `${period.year}-BW${String(period.biweek).padStart(2, '0')}`;
        case 'monthly':
            return `${period.year}-${String(period.month).padStart(2, '0')}`;
        case 'quarterly':
            return `${period.year}-Q${period.quarter}`;
        default:
            return '';
    }
}

function keyToPeriod(key) {
    if (!key) return null;
    
    if (key.includes('-W')) {
        const [year, week] = key.split('-W');
        return { year: parseInt(year), week: parseInt(week), type: 'weekly' };
    } else if (key.includes('-BW')) {
        const [year, biweek] = key.split('-BW');
        return { year: parseInt(year), biweek: parseInt(biweek), type: 'biweekly' };
    } else if (key.includes('-Q')) {
        const [year, quarter] = key.split('-Q');
        return { year: parseInt(year), quarter: parseInt(quarter), type: 'quarterly' };
    } else {
        const [year, month] = key.split('-');
        return { year: parseInt(year), month: parseInt(month), type: 'monthly' };
    }
}

// ============================================
// EDIT PERIOD SELECTOR FUNCTIONS
// ============================================

function updateEditPeriodSelector() {
    const periodType = document.getElementById('editPeriodType').value;
    const container = document.getElementById('editPeriodSelectors');
    
    // Initialize with current year or from edit state
    const year = editPeriodState?.year || new Date().getFullYear();
    
    let period;
    switch (periodType) {
        case 'weekly':
            period = { year, week: editPeriodState?.week || 1, type: 'weekly' };
            break;
        case 'biweekly':
            period = { year, biweek: editPeriodState?.biweek || 1, type: 'biweekly' };
            break;
        case 'monthly':
            period = { year, month: editPeriodState?.month || 1, type: 'monthly' };
            break;
        case 'quarterly':
            period = { year, quarter: editPeriodState?.quarter || 1, type: 'quarterly' };
            break;
    }
    
    editPeriodState = period;
    renderPeriodSelector(container, periodType, period, true);
    updateEditPeriodDisplay();
}

function onYearChangeEdit() {
    const periodType = document.getElementById('editPeriodType').value;
    const year = parseInt(document.getElementById('editperiodYear')?.value) || new Date().getFullYear();
    const container = document.getElementById('editPeriodSelectors');
    
    // Preserve current selection if possible
    let currentValue = 1;
    switch (periodType) {
        case 'weekly':
            currentValue = parseInt(document.getElementById('editperiodWeek')?.value) || 1;
            break;
        case 'biweekly':
            currentValue = parseInt(document.getElementById('editperiodBiweek')?.value) || 1;
            break;
        case 'monthly':
            currentValue = parseInt(document.getElementById('editperiodMonth')?.value) || 1;
            break;
        case 'quarterly':
            currentValue = parseInt(document.getElementById('editperiodQuarter')?.value) || 1;
            break;
    }
    
    // Adjust if out of range for new year
    if (periodType === 'weekly') {
        const weeksInYear = getWeeksInYear(year);
        currentValue = Math.min(currentValue, weeksInYear);
    } else if (periodType === 'biweekly') {
        const biweeksInYear = Math.ceil(getWeeksInYear(year) / 2);
        currentValue = Math.min(currentValue, biweeksInYear);
    }
    
    editPeriodState = {
        year,
        type: periodType,
        ...(periodType === 'weekly' && { week: currentValue }),
        ...(periodType === 'biweekly' && { biweek: currentValue }),
        ...(periodType === 'monthly' && { month: currentValue }),
        ...(periodType === 'quarterly' && { quarter: currentValue })
    };
    
    renderPeriodSelector(container, periodType, editPeriodState, true);
    updateEditPeriodDisplay();
}

function updateEditSelectedPeriod() {
    const periodType = document.getElementById('editPeriodType').value;
    const year = parseInt(document.getElementById('editperiodYear')?.value) || new Date().getFullYear();
    
    switch (periodType) {
        case 'weekly':
            const week = parseInt(document.getElementById('editperiodWeek')?.value) || 1;
            editPeriodState = { year, week, type: 'weekly' };
            break;
        case 'biweekly':
            const biweek = parseInt(document.getElementById('editperiodBiweek')?.value) || 1;
            editPeriodState = { year, biweek, type: 'biweekly' };
            break;
        case 'monthly':
            const month = parseInt(document.getElementById('editperiodMonth')?.value) || 1;
            editPeriodState = { year, month, type: 'monthly' };
            break;
        case 'quarterly':
            const quarter = parseInt(document.getElementById('editperiodQuarter')?.value) || 1;
            editPeriodState = { year, quarter, type: 'quarterly' };
            break;
    }
    
    updateEditPeriodDisplay();
}

function updateEditPeriodDisplay() {
    const display = document.getElementById('editPeriodDisplay');
    if (display && editPeriodState) {
        display.textContent = formatPeriodDisplayText(editPeriodState);
    }
}

function getEditPeriodKey() {
    if (!editPeriodState) return '';
    return periodToKey(editPeriodState);
}

// ============================================
// KID MANAGEMENT FUNCTIONS
// ============================================

function renderKidsList(kids) {
    const container = document.getElementById('kidsList');
    
    if (!kids || kids.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">👶</div>
                <p>No kids added yet. Add your first kid above!</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = kids.map(kid => `
        <div class="kid-card" onclick="selectKid('${kid.id}')">
            <div class="kid-card-header">
                <h3>👦 ${escapeHtml(kid.name)}</h3>
                <div class="kid-card-actions" onclick="event.stopPropagation()">
                    <button class="edit-btn" onclick="openEditModal('${kid.id}', '${escapeHtml(kid.name)}')" title="Edit">✏️</button>
                    <button class="delete-btn" onclick="openDeleteModal('${kid.id}', '${escapeHtml(kid.name)}')" title="Delete">🗑️</button>
                </div>
            </div>
            <div class="kid-card-totals">
                <div class="total-item spent">
                    <span class="total-label">Spent</span>
                    <span class="total-value">${formatCurrency(kid.totals?.totalSpent || 0)}</span>
                </div>
                <div class="total-item saved">
                    <span class="total-label">Saved</span>
                    <span class="total-value">${formatCurrency(kid.totals?.totalSaved || 0)}</span>
                </div>
                <div class="total-item given">
                    <span class="total-label">Given</span>
                    <span class="total-value">${formatCurrency(kid.totals?.totalGiven || 0)}</span>
                </div>
            </div>
        </div>
    `).join('');
}

async function addKid() {
    const nameInput = document.getElementById('newKidName');
    const name = nameInput.value.trim();
    
    if (!name) {
        showToast('Please enter a name', 'error');
        return;
    }
    
    try {
        await apiCall('api.php?action=addKid', 'POST', { name });
        nameInput.value = '';
        loadKids();
        showToast(`${name} has been added!`, 'success');
    } catch (error) {
        console.error('Failed to add kid:', error);
    }
}

async function selectKid(kidId) {
    try {
        const result = await apiCall(`api.php?action=getKid&id=${kidId}`);
        currentKid = result.kid;
        showKidDetails();
    } catch (error) {
        console.error('Failed to load kid details:', error);
    }
}

function showKidDetails() {
    if (!currentKid) return;
    
    document.querySelector('.kids-management').style.display = 'none';
    document.getElementById('kidDetails').style.display = 'block';
    
    document.getElementById('selectedKidName').textContent = `👦 ${currentKid.name}'s Pocket Money`;
    
    document.getElementById('spentPercent').value = currentKid.allocation.spent;
    document.getElementById('savedPercent').value = currentKid.allocation.saved;
    document.getElementById('givenPercent').value = currentKid.allocation.given;
    document.getElementById('interestRate').value = currentKid.interestRate || 0;
    
    // Reset used from saved field
    document.getElementById('entryUsedFromSaved').value = 0;
    
    initializePeriodSelector();
    updateTotalsDisplay();
    updateAvailableSavedDisplay(); // Add this line
    renderEntriesTable();
    updateChart();
}

function closeKidDetails() {
    document.getElementById('kidDetails').style.display = 'none';
    document.querySelector('.kids-management').style.display = 'block';
    currentKid = null;
    loadKids();
}

function validateAllocation() {
    const spent = parseFloat(document.getElementById('spentPercent').value) || 0;
    const saved = parseFloat(document.getElementById('savedPercent').value) || 0;
    const given = parseFloat(document.getElementById('givenPercent').value) || 0;
    const total = spent + saved + given;
    
    const errorDiv = document.getElementById('allocationError');
    
    if (Math.abs(total - 100) > 0.01) {
        errorDiv.textContent = `Total must be 100% (currently ${total.toFixed(1)}%)`;
        return false;
    } else {
        errorDiv.textContent = '';
        return true;
    }
}

async function saveAllocation() {
    if (!validateAllocation() || !currentKid) return;
    
    const data = {
        kidId: currentKid.id,
        spent: parseFloat(document.getElementById('spentPercent').value),
        saved: parseFloat(document.getElementById('savedPercent').value),
        given: parseFloat(document.getElementById('givenPercent').value),
        interestRate: parseFloat(document.getElementById('interestRate').value) || 0
    };
    
    try {
        await apiCall('api.php?action=updateAllocation', 'PUT', data);
        currentKid.allocation = {
            spent: data.spent,
            saved: data.saved,
            given: data.given
        };
        currentKid.interestRate = data.interestRate;
        showToast('Default allocation saved!', 'success');
    } catch (error) {
        console.error('Failed to save allocation:', error);
    }
}

async function addEntry() {
    if (!currentKid) return;
    
    const period = getPeriodKey();
    const amount = parseFloat(document.getElementById('entryAmount').value);
    const usedFromSaved = parseFloat(document.getElementById('entryUsedFromSaved').value) || 0;
    const interestRate = parseFloat(document.getElementById('interestRate').value) || 0;
    
    if (!period) {
        showToast('Please select a period', 'error');
        return;
    }
    
    if (!amount || amount <= 0) {
        showToast('Please enter a valid amount', 'error');
        return;
    }
    
    // Validate usedFromSaved
    const availableSaved = currentKid.totals?.currentSaved || 0;
    // Account for interest that will be applied
    const interestOnSaved = availableSaved * (interestRate / 100);
    const totalAvailable = availableSaved + interestOnSaved;
    
    if (usedFromSaved < 0) {
        showToast('Used from saved cannot be negative', 'error');
        return;
    }
    
    if (usedFromSaved > totalAvailable) {
        showToast(`Cannot use more than available (${formatCurrency(totalAvailable)} available)`, 'error');
        return;
    }
    
    try {
        await apiCall('api.php?action=addEntry', 'POST', {
            kidId: currentKid.id,
            period,
            periodType: currentPeriodType,
            amount,
            interestRate,
            usedFromSaved,
            spentPercent: currentKid.allocation.spent,
            savedPercent: currentKid.allocation.saved,
            givenPercent: currentKid.allocation.given
        });
        
        await selectKid(currentKid.id);
        document.getElementById('entryAmount').value = '';
        document.getElementById('entryUsedFromSaved').value = 0;
        showToast('Entry added!', 'success');
    } catch (error) {
        console.error('Failed to add entry:', error);
    }
}

function updateTotalsDisplay() {
    if (!currentKid || !currentKid.totals) return;
    
    const totals = currentKid.totals;
    
    // Total spent now includes used from saved
    const totalSpentDisplay = document.getElementById('totalSpent');
    const usedFromSaved = totals.totalUsedFromSaved || 0;
    const allocatedSpent = totals.totalAllocatedSpent || 0;
    
    if (usedFromSaved > 0) {
        totalSpentDisplay.innerHTML = `
            ${formatCurrency(totals.totalSpent)}
            <span class="total-breakdown">(${formatCurrency(allocatedSpent)} + ${formatCurrency(usedFromSaved)} from saved)</span>
        `;
    } else {
        totalSpentDisplay.textContent = formatCurrency(totals.totalSpent);
    }
    
    document.getElementById('totalSaved').textContent = formatCurrency(totals.totalSaved);
    document.getElementById('totalGiven').textContent = formatCurrency(totals.totalGiven);
    document.getElementById('grandTotal').textContent = formatCurrency(totals.grandTotal);
}

function renderEntriesTable() {
    const tbody = document.getElementById('entriesBody');
    const entries = currentKid?.totals?.entries || [];
    
    if (entries.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="9" style="text-align: center; padding: 40px; color: var(--text-muted);">
                    No entries yet. Add your first entry above!
                </td>
            </tr>
        `;
        return;
    }
    
    const sortedEntries = [...entries].sort((a, b) => b.period.localeCompare(a.period));
    
    tbody.innerHTML = sortedEntries.map(entry => {
        const usedFromSaved = entry.usedFromSaved || 0;
        const usedClass = usedFromSaved > 0 ? 'used-from-saved' : 'used-from-saved zero';
        
        return `
        <tr>
            <td><strong>${formatPeriodLabel(entry.period)}</strong></td>
            <td><strong>${formatCurrency(entry.amount)}</strong></td>
            <td>
                <div class="entry-allocation spent-value">
                    <span class="percent">${entry.spentPercent || 0}%</span>
                    <span class="amount">${formatCurrency(entry.spent)}</span>
                </div>
            </td>
            <td>
                <div class="entry-allocation saved-value">
                    <span class="percent">${entry.savedPercent || 0}%</span>
                    <span class="amount">${formatCurrency(entry.saved)}</span>
                </div>
            </td>
            <td>
                <div class="entry-allocation given-value">
                    <span class="percent">${entry.givenPercent || 0}%</span>
                    <span class="amount">${formatCurrency(entry.given)}</span>
                </div>
            </td>
            <td>
                <div class="entry-allocation interest-value">
                    <span class="percent">${entry.interestRate || 0}%</span>
                    <span class="amount">+${formatCurrency(entry.interestEarned || 0)}</span>
                </div>
            </td>
            <td class="${usedClass}">
                ${usedFromSaved > 0 ? '-' : ''}${formatCurrency(usedFromSaved)}
            </td>
            <td class="running-saved">${formatCurrency(entry.runningSaved || 0)}</td>
            <td>
                <div class="entry-actions">
                    <button class="btn btn-sm btn-primary btn-icon" onclick="openEditEntryModal('${entry.id}')" title="Edit Entry">✏️</button>
                    <button class="btn btn-sm btn-danger btn-icon" onclick="deleteEntry('${entry.id}')" title="Delete">🗑️</button>
                </div>
            </td>
        </tr>
    `}).join('');
}

function formatPeriodLabel(period) {
    if (!period) return '';
    
    if (period.includes('-W')) {
        const [year, week] = period.split('-W');
        return `Week ${parseInt(week)}, ${year}`;
    } else if (period.includes('-BW')) {
        const [year, biweek] = period.split('-BW');
        return `Period ${parseInt(biweek)}, ${year}`;
    } else if (period.includes('-Q')) {
        const [year, quarter] = period.split('-Q');
        return `Q${quarter} ${year}`;
    } else {
        const [year, month] = period.split('-');
        const date = new Date(year, parseInt(month) - 1);
        return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short' });
    }
}

// ============================================
// EDIT ENTRY MODAL FUNCTIONS
// ============================================

function openEditEntryModal(entryId) {
    if (!currentKid) return;
    
    const entries = currentKid.totals?.entries || [];
    const entry = entries.find(e => e.id === entryId);
    
    if (!entry) {
        showToast('Entry not found', 'error');
        return;
    }
    
    editingEntryData = { ...entry };
    
    document.getElementById('editEntryId').value = entryId;
    document.getElementById('editEntryOriginalPeriod').value = entry.period;
    document.getElementById('editEntryAmount').value = entry.amount;
    document.getElementById('editUsedFromSaved').value = entry.usedFromSaved || 0;
    
    // Calculate and display available saved at this entry's point
    // Available = runningSaved (after this entry) + usedFromSaved (what was used) - saved (what was added)
    const availableAtEntry = (entry.runningSaved || 0) + (entry.usedFromSaved || 0);
    document.getElementById('editAvailableSavedAmount').textContent = formatCurrency(availableAtEntry);
    document.getElementById('editUsedFromSaved').max = availableAtEntry;
    
    document.getElementById('editSpentPercent').value = entry.spentPercent || 0;
    document.getElementById('editSavedPercent').value = entry.savedPercent || 0;
    document.getElementById('editGivenPercent').value = entry.givenPercent || 0;
    document.getElementById('editInterestRate').value = entry.interestRate || 0;
    
    // Parse the period and set up the period selector
    editPeriodState = keyToPeriod(entry.period);
    document.getElementById('editPeriodType').value = editPeriodState?.type || 'monthly';
    
    // Render the period selectors
    const container = document.getElementById('editPeriodSelectors');
    renderPeriodSelector(container, editPeriodState?.type || 'monthly', editPeriodState, true);
    
    validateAndUpdateEditEntry();
    
    document.getElementById('editEntryModal').classList.add('active');
}

function validateAndUpdateEditEntry() {
    const amount = parseFloat(document.getElementById('editEntryAmount').value) || 0;
    const spent = parseFloat(document.getElementById('editSpentPercent').value) || 0;
    const saved = parseFloat(document.getElementById('editSavedPercent').value) || 0;
    const given = parseFloat(document.getElementById('editGivenPercent').value) || 0;
    const usedFromSaved = parseFloat(document.getElementById('editUsedFromSaved').value) || 0;
    const total = spent + saved + given;
    
    const errorDiv = document.getElementById('editAllocationError');
    const totalDiv = document.getElementById('editAllocationTotal');
    
    totalDiv.textContent = `${total.toFixed(1)}%`;
    totalDiv.parentElement.classList.remove('error', 'valid');
    
    // Calculate amounts
    const spentAmount = amount * spent / 100;
    const savedAmount = amount * saved / 100;
    const givenAmount = amount * given / 100;
    
    // Update calculated amounts display
    document.getElementById('editSpentAmount').textContent = `= ${formatCurrency(spentAmount)}`;
    document.getElementById('editSavedAmount').textContent = `= ${formatCurrency(savedAmount)}`;
    document.getElementById('editGivenAmount').textContent = `= ${formatCurrency(givenAmount)}`;
    
    // Update summary
    document.getElementById('summarySpent').textContent = formatCurrency(spentAmount);
    document.getElementById('summarySaved').textContent = formatCurrency(savedAmount);
    document.getElementById('summaryGiven').textContent = formatCurrency(givenAmount);
    
    // Validate
    const maxUsedFromSaved = parseFloat(document.getElementById('editUsedFromSaved').max) || 0;
    
    if (Math.abs(total - 100) > 0.01) {
        errorDiv.textContent = `Allocation must total 100%`;
        totalDiv.parentElement.classList.add('error');
        return false;
    } else if (amount <= 0) {
        errorDiv.textContent = `Amount must be greater than 0`;
        totalDiv.parentElement.classList.add('error');
        return false;
    } else if (usedFromSaved < 0) {
        errorDiv.textContent = `Used from saved cannot be negative`;
        totalDiv.parentElement.classList.add('error');
        return false;
    } else if (usedFromSaved > maxUsedFromSaved) {
        errorDiv.textContent = `Cannot use more than ${formatCurrency(maxUsedFromSaved)} from saved`;
        totalDiv.parentElement.classList.add('error');
        return false;
    } else {
        errorDiv.textContent = '';
        totalDiv.parentElement.classList.add('valid');
        return true;
    }
}

async function saveEntryChanges() {
    if (!validateAndUpdateEditEntry() || !currentKid) return;
    
    const entryId = document.getElementById('editEntryId').value;
    const newPeriodKey = getEditPeriodKey();
    const periodType = document.getElementById('editPeriodType').value;
    
    const data = {
        kidId: currentKid.id,
        entryId,
        period: newPeriodKey,
        periodType: periodType,
        amount: parseFloat(document.getElementById('editEntryAmount').value),
        usedFromSaved: parseFloat(document.getElementById('editUsedFromSaved').value) || 0,
        spentPercent: parseFloat(document.getElementById('editSpentPercent').value),
        savedPercent: parseFloat(document.getElementById('editSavedPercent').value),
        givenPercent: parseFloat(document.getElementById('editGivenPercent').value),
        interestRate: parseFloat(document.getElementById('editInterestRate').value) || 0
    };
    
    try {
        await apiCall('api.php?action=updateEntry', 'PUT', data);
        closeModal('editEntryModal');
        await selectKid(currentKid.id);
        showToast('Entry updated!', 'success');
    } catch (error) {
        console.error('Failed to update entry:', error);
    }
}

async function deleteEntry(entryId) {
    if (!currentKid) return;
    
    if (!confirm('Are you sure you want to delete this entry?')) {
        return;
    }
    
    try {
        await apiCall(`api.php?action=deleteEntry&kidId=${currentKid.id}&entryId=${entryId}`, 'DELETE');
        await selectKid(currentKid.id);
        showToast('Entry deleted!', 'success');
    } catch (error) {
        console.error('Failed to delete entry:', error);
    }
}

// ============================================
// CHART FUNCTIONS
// ============================================

function updateChart() {
    const canvas = document.getElementById('savingsChart');
    const entries = currentKid?.totals?.entries || [];
    
    if (chart) {
        chart.destroy();
    }
    
    if (entries.length === 0) {
        return;
    }
    
    const sortedEntries = [...entries].sort((a, b) => a.period.localeCompare(b.period));
    
    const labels = sortedEntries.map(e => formatPeriodLabel(e.period));
    
    let cumulativeSpent = 0;
    let cumulativeGiven = 0;
    
    const spentData = sortedEntries.map(e => {
        cumulativeSpent += e.spent;
        return cumulativeSpent;
    });
    
    const savedData = sortedEntries.map(e => e.runningSaved || 0);
    
    const givenData = sortedEntries.map(e => {
        cumulativeGiven += e.given;
        return cumulativeGiven;
    });
    
    chart = new Chart(canvas, {
        type: 'line',
        data: {
            labels,
            datasets: [
                {
                    label: 'Cumulative Spent',
                    data: spentData,
                    borderColor: '#f97316',
                    backgroundColor: 'rgba(249, 115, 22, 0.1)',
                    fill: true,
                    tension: 0.3
                },
                {
                    label: 'Total Saved (with interest)',
                    data: savedData,
                    borderColor: '#22c55e',
                    backgroundColor: 'rgba(34, 197, 94, 0.1)',
                    fill: true,
                    tension: 0.3
                },
                {
                    label: 'Cumulative Given',
                    data: givenData,
                    borderColor: '#8b5cf6',
                    backgroundColor: 'rgba(139, 92, 246, 0.1)',
                    fill: true,
                    tension: 0.3
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: 'Savings Evolution Over Time'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${formatCurrency(context.raw)}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return formatCurrency(value);
                        }
                    }
                }
            }
        }
    });
}

// ============================================
// MODAL FUNCTIONS
// ============================================

function openEditModal(kidId, kidName) {
    document.getElementById('editKidId').value = kidId;
    document.getElementById('editKidName').value = kidName;
    document.getElementById('editKidModal').classList.add('active');
}

function openDeleteModal(kidId, kidName) {
    document.getElementById('deleteKidId').value = kidId;
    document.getElementById('deleteConfirmText').textContent = 
        `Are you sure you want to delete "${kidName}"? All their data will be lost.`;
    document.getElementById('confirmDeleteModal').classList.add('active');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
    if (modalId === 'editEntryModal') {
        editingEntryData = null;
        editPeriodState = null;
    }
}

async function saveKidName() {
    const kidId = document.getElementById('editKidId').value;
    const name = document.getElementById('editKidName').value.trim();
    
    if (!name) {
        showToast('Please enter a name', 'error');
        return;
    }
    
    try {
        await apiCall('api.php?action=updateKid', 'PUT', { id: kidId, name });
        closeModal('editKidModal');
        loadKids();
        showToast('Name updated!', 'success');
    } catch (error) {
        console.error('Failed to update kid name:', error);
    }
}

async function confirmDeleteKid() {
    const kidId = document.getElementById('deleteKidId').value;
    
    try {
        await apiCall(`api.php?action=deleteKid&id=${kidId}`, 'DELETE');
        closeModal('confirmDeleteModal');
        loadKids();
        showToast('Kid removed successfully', 'success');
    } catch (error) {
        console.error('Failed to delete kid:', error);
    }
}

// ============================================
// UTILITY FUNCTIONS
// ============================================

function formatCurrency(amount) {
    return new Intl.NumberFormat('en-EU', {
        style: 'currency',
        currency: 'EUR',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(amount);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showToast(message, type = 'success') {
    const existingToast = document.querySelector('.toast');
    if (existingToast) {
        existingToast.remove();
    }
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => toast.classList.add('show'), 10);
    
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Update available saved amount display
function updateAvailableSavedDisplay() {
    const availableEl = document.getElementById('availableSavedAmount');
    if (availableEl && currentKid) {
        const available = currentKid.totals?.currentSaved || 0;
        availableEl.textContent = formatCurrency(available);
        
        // Update max attribute on input
        const input = document.getElementById('entryUsedFromSaved');
        if (input) {
            input.max = available;
        }
    }
}


// Close modals when clicking outside
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal')) {
        e.target.classList.remove('active');
        if (e.target.id === 'editEntryModal') {
            editingEntryData = null;
            editPeriodState = null;
        }
    }
});

// Handle Enter key in input fields
document.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        if (e.target.id === 'newKidName') {
            addKid();
        } else if (e.target.id === 'editKidName') {
            saveKidName();
        } else if (e.target.id === 'entryAmount') {
            addEntry();
        }
    }
});