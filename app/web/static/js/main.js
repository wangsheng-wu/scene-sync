// Global variables
let currentResults = null;
let currentOutputFile = null;
let currentTruthFiles = [];
let charts = {};
let currentFilmFolder = null;
let currentSceneFolder = null;

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    loadFolders();
    loadTruthFiles();
    loadReferenceTables();
    setupEventListeners();
    // Set initial state of visualizations toggle
    document.getElementById('toggleVisualizations').checked = document.getElementById('visualizationsSection').style.display === 'block';

    // Collapse icon toggle for verification results
    const verificationCollapse = document.getElementById('verificationCollapse');
    const verificationCollapseIcon = document.getElementById('verificationCollapseIcon');
    if (verificationCollapse && verificationCollapseIcon) {
        verificationCollapse.addEventListener('show.bs.collapse', function () {
            verificationCollapseIcon.classList.remove('fa-chevron-down');
            verificationCollapseIcon.classList.add('fa-chevron-up');
        });
        verificationCollapse.addEventListener('hide.bs.collapse', function () {
            verificationCollapseIcon.classList.remove('fa-chevron-up');
            verificationCollapseIcon.classList.add('fa-chevron-down');
        });
    }
});

// Load available folders
async function loadFolders() {
    try {
        const response = await fetch('/api/folders');
        const data = await response.json();
        
        if (data.success) {
            populateFolderSelect('filmFolder', data.film_folders);
            populateFolderSelect('sceneFolder', data.scene_folders);
        } else {
            showError('Failed to load folders: ' + data.error);
        }
    } catch (error) {
        showError('Failed to load folders: ' + error.message);
    }
}

// Populate folder select dropdown
function populateFolderSelect(selectId, folders) {
    const select = document.getElementById(selectId);
    select.innerHTML = '<option value="">Select a folder...</option>';
    
    folders.forEach(folder => {
        const option = document.createElement('option');
        option.value = folder;
        option.textContent = folder;
        select.appendChild(option);
    });
}

// Setup event listeners
function setupEventListeners() {
    // Form submission
    document.getElementById('matchingForm').addEventListener('submit', handleMatchSubmit);
    
    // Folder selection changes
    document.getElementById('filmFolder').addEventListener('change', updateFolderInfo);
    document.getElementById('sceneFolder').addEventListener('change', updateFolderInfo);
    
    // Download button
    document.getElementById('downloadBtn').addEventListener('click', downloadResults);
    
    // Verify button
    document.getElementById('verifyBtn').addEventListener('click', showVerificationModal);
    
    // Inspect button
    document.getElementById('inspectBtn').addEventListener('click', showInspectionSection);
    
    // Inspect images button
    document.getElementById('inspectButton').addEventListener('click', inspectImages);

    // Visualizations toggle
    document.getElementById('toggleVisualizations').addEventListener('change', function() {
        document.getElementById('visualizationsSection').style.display = this.checked ? 'block' : 'none';
    });
}

// Handle form submission
async function handleMatchSubmit(event) {
    event.preventDefault();
    
    const filmFolder = document.getElementById('filmFolder').value;
    const sceneFolder = document.getElementById('sceneFolder').value;
    const maxFeatures = parseInt(document.getElementById('maxFeatures').value);
    const goodMatchPercent = parseFloat(document.getElementById('goodMatchPercent').value);
    const referenceTable = document.getElementById('referenceTable').value;
    
    if (!filmFolder || !sceneFolder) {
        showError('Please select both film and scene folders');
        return;
    }
    
    // Clear previous verification results and charts
    clearVerificationResults();
    clearCharts();
    
    // Hide inspection results when starting a new match
    const inspectionResults = document.getElementById('inspectionResults');
    if (inspectionResults) inspectionResults.style.display = 'none';
    const img = document.getElementById('visualizationImg');
    if (img) img.src = '';
    // Hide the entire inspection section when starting a new match
    const inspectionSection = document.getElementById('inspectionSection');
    if (inspectionSection) inspectionSection.style.display = 'none';
    
    // Show loading
    showLoading(true);
    
    try {
        const response = await fetch('/api/match', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                film_folder: filmFolder,
                scene_folder: sceneFolder,
                max_features: maxFeatures,
                good_match_percent: goodMatchPercent,
                reference_table: referenceTable
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentResults = data.results;
            currentOutputFile = data.output_file.split('/').pop();
            
            // Store current folders for inspection
            currentFilmFolder = filmFolder;
            currentSceneFolder = sceneFolder;
            
            // Show reference table info if used
            let resultMessage = `Found ${data.total_matches} matches`;
            if (data.existing_matches > 0) {
                resultMessage += ` (${data.existing_matches} from reference, ${data.new_matches} new)`;
            }
            
            displayResults(data.results, data.total_matches, resultMessage);
            createVisualizations(data.results);
            // Show the toggle switch after a successful match
            document.getElementById('toggleVisualizationsContainer').style.display = 'block';
        } else {
            showError('Matching failed: ' + data.error);
        }
    } catch (error) {
        showError('Matching failed: ' + error.message);
    } finally {
        showLoading(false);
    }
}

// Display results
function displayResults(results, totalMatches, resultMessage = null) {
    const resultsContent = document.getElementById('resultsContent');
    
    if (results.length === 0) {
        resultsContent.innerHTML = `
            <div class="text-center text-muted py-4">
                <i class="fas fa-exclamation-triangle fa-3x mb-3"></i>
                <p>No matches found with sufficient confidence</p>
            </div>
        `;
        return;
    }
    
    const message = resultMessage || `Found ${totalMatches} matches`;
    let html = `
        <div class="d-flex justify-content-between align-items-center mb-3">
            <h6>${message}</h6>
            <span class="badge bg-primary">${results.length} results</span>
        </div>
        <div class="table-responsive results-table">
            <table class="table table-striped">
                <thead>
                    <tr>
                        <th>Film Photo</th>
                        <th>Scene Photo</th>
                        <th>Confidence</th>
                        <th>Status</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    results.forEach((result, index) => {
        const confidenceClass = getConfidenceClass(result.confidence_score);
        let statusBadge;
        
        if (result.confident_match === 1) {
            statusBadge = '<span class="badge bg-success">Confident</span>';
        } else if (result.confident_match === -1) {
            statusBadge = '<span class="badge bg-secondary">Deferred</span>';
        } else {
            statusBadge = '<span class="badge bg-warning">Maybe</span>';
        }
        
        const scenePhoto = result.scene_photo || 'No match';
        const inspectButton = result.scene_photo ? 
            `<button class="btn btn-sm btn-outline-info" onclick="inspectMatchedPair('${result.film_photo}', '${result.scene_photo}')">
                <i class="fas fa-search"></i> Inspect
            </button>` : 
            '<span class="text-muted">-</span>';
        
        html += `
            <tr>
                <td><code>${result.film_photo}</code></td>
                <td><code>${scenePhoto}</code></td>
                <td><span class="${confidenceClass}">${(result.confidence_score * 100).toFixed(1)}%</span></td>
                <td>${statusBadge}</td>
                <td>${inspectButton}</td>
            </tr>
        `;
    });
    
    html += `
            </tbody>
        </table>
    </div>
    `;
    
    resultsContent.innerHTML = html;
}

// Create visualizations
function createVisualizations(results) {
    if (results.length === 0) return;
    
    // Only show if toggle is ON
    if (document.getElementById('toggleVisualizations').checked) {
        document.getElementById('visualizationsSection').style.display = 'block';
    } else {
        document.getElementById('visualizationsSection').style.display = 'none';
    }
    
    // Create match status chart
    createMatchStatusChart(results);
    
    // Create confidence distribution chart
    createConfidenceChart(results);
}

// Create match status pie chart
function createMatchStatusChart(results) {
    const ctx = document.getElementById('matchStatusChart').getContext('2d');
    
    // Count match statuses
    const statusCounts = {
        confident: 0,
        lowConfidence: 0,
        deferred: 0
    };
    
    results.forEach(result => {
        if (result.confident_match === 1) {
            statusCounts.confident++;
        } else if (result.confident_match === -1) {
            statusCounts.deferred++;
        } else {
            statusCounts.lowConfidence++;
        }
    });
    
    // Destroy existing chart if it exists
    if (charts.matchStatus) {
        charts.matchStatus.destroy();
    }
    
    charts.matchStatus = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Confident', 'Low Confidence', 'Deferred'],
            datasets: [{
                data: [statusCounts.confident, statusCounts.lowConfidence, statusCounts.deferred],
                backgroundColor: ['#28a745', '#ffc107', '#6c757d'],
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

// Create confidence distribution histogram
function createConfidenceChart(results) {
    const ctx = document.getElementById('confidenceChart').getContext('2d');
    
    // Create confidence bins
    const bins = [0, 0.2, 0.4, 0.6, 0.7, 0.8, 0.9, 1.0];
    const binCounts = [0, 0, 0, 0, 0, 0, 0, 0];
    
    results.forEach(result => {
        const confidence = result.confidence_score;
        for (let i = 0; i < bins.length - 1; i++) {
            if (confidence >= bins[i] && confidence < bins[i + 1]) {
                binCounts[i]++;
                break;
            }
        }
    });
    
    // Destroy existing chart if it exists
    if (charts.confidence) {
        charts.confidence.destroy();
    }
    
    charts.confidence = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['0-20%', '20-40%', '40-60%', '60-70%', '70-80%', '80-90%', '90-100%'],
            datasets: [{
                label: 'Number of Matches',
                data: binCounts,
                backgroundColor: [
                    '#6c757d', // Gray for low confidence (0-20%)
                    '#6c757d', // Gray for low confidence (20-40%)
                    '#6c757d', // Gray for low confidence (40-60%)
                    '#ffc107', // Yellow for medium confidence (60-70%)
                    '#28a745', // Green for high confidence (70-80%)
                    '#28a745', // Green for high confidence (80-90%)
                    '#28a745'  // Green for high confidence (90-100%)
                ],
                borderColor: [
                    '#495057', '#495057', '#495057', '#e0a800', '#1e7e34', '#1e7e34', '#1e7e34'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}

// Clear all charts
function clearCharts() {
    Object.values(charts).forEach(chart => {
        if (chart) {
            chart.destroy();
        }
    });
    charts = {};
    document.getElementById('visualizationsSection').style.display = 'none';
}

// Get confidence class for styling
function getConfidenceClass(score) {
    if (score >= 0.7) return 'confidence-high';
    if (score >= 0.5) return 'confidence-medium';
    return 'confidence-low';
}

// Show/hide loading
function showLoading(show) {
    const loading = document.getElementById('loading');
    const resultsContent = document.getElementById('resultsContent');
    
    if (show) {
        loading.style.display = 'block';
        resultsContent.style.display = 'none';
    } else {
        loading.style.display = 'none';
        resultsContent.style.display = 'block';
    }
}

// Show error message
function showError(message) {
    const resultsContent = document.getElementById('resultsContent');
    resultsContent.innerHTML = `
        <div class="alert alert-danger">
            <i class="fas fa-exclamation-triangle"></i> ${message}
        </div>
    `;
}

// Load truth files
async function loadTruthFiles() {
    try {
        const response = await fetch('/api/truth-files');
        const data = await response.json();
        
        if (data.success) {
            currentTruthFiles = data.truth_files;
        }
    } catch (error) {
        console.error('Error loading truth files:', error);
    }
}

// Load reference tables
async function loadReferenceTables() {
    try {
        const response = await fetch('/api/reference-tables');
        const data = await response.json();
        
        if (data.success) {
            const select = document.getElementById('referenceTable');
            select.innerHTML = '<option value="">No reference table</option>';
            
            data.reference_tables.forEach(table => {
                const option = document.createElement('option');
                option.value = table;
                option.textContent = table;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading reference tables:', error);
    }
}

// Show verification modal
function showVerificationModal() {
    console.log('Verification modal triggered');
    console.log('Current truth files:', currentTruthFiles);
    
    if (currentTruthFiles.length === 0) {
        alert('No truth files found. Please add CSV files to the truth/ directory.');
        return;
    }
    // Populate dropdown
    const select = document.getElementById('truthFileSelect');
    select.innerHTML = '';
    currentTruthFiles.forEach(file => {
        const option = document.createElement('option');
        option.value = file;
        option.textContent = file;
        select.appendChild(option);
    });
    // Show modal
    const verifyModal = new bootstrap.Modal(document.getElementById('verifyModal'));
    verifyModal.show();
    // Set up confirm button
    document.getElementById('confirmVerifyBtn').onclick = function() {
        const selectedFile = select.value;
        console.log('Selected truth file:', selectedFile);
        verifyModal.hide();
        verifyResults(selectedFile);
    };
}

// Verify results
async function verifyResults(truthFile) {
    console.log('Starting verification with:', { results_file: currentOutputFile, truth_file: truthFile });
    try {
        const response = await fetch('/api/verify', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                results_file: currentOutputFile,
                truth_file: truthFile
            })
        });
        
        const data = await response.json();
        console.log('Verification response:', data);
        
        if (data.success) {
            displayVerificationResults(data.metrics, data.detailed_results);
        } else {
            alert('Verification failed: ' + data.error);
        }
    } catch (error) {
        console.error('Verification error:', error);
        alert('Verification failed: ' + error.message);
    }
}

// Display verification results
function displayVerificationResults(metrics, detailedResults) {
    const verificationContent = document.getElementById('verificationContent');
    const verificationMetrics = document.getElementById('verificationMetrics');
    
    let html = `
        <div class="row">
            <div class="col-md-6">
                <h6>Summary</h6>
                <ul class="list-unstyled">
                    <li><strong>Total Results:</strong> ${metrics.total_results}</li>
                    <li><strong>Total Truth:</strong> ${metrics.total_truth}</li>
                </ul>
            </div>
            <div class="col-md-6">
                <h6>Metrics</h6>
                <ul class="list-unstyled">
                    <li><strong>Accuracy:</strong> ${(metrics.accuracy * 100).toFixed(1)}%</li>
                    <li><strong>Precision:</strong> ${(metrics.precision * 100).toFixed(1)}%</li>
                    <li><strong>Recall:</strong> ${(metrics.recall * 100).toFixed(1)}%</li>
                    <li><strong>F1 Score:</strong> ${metrics.f1_score.toFixed(3)}</li>
                </ul>
            </div>
        </div>
        <div class="row mt-3">
            <div class="col-12">
                <h6>Matching Details</h6>
                <ul class="list-unstyled">
                    <li class="text-success"><strong>Correct:</strong> ${metrics.correct_matches}</li>
                    <li class="text-danger"><strong>Incorrect:</strong> ${metrics.incorrect_matches}</li>
                    <li class="text-warning"><strong>Missed:</strong> ${metrics.missed_matches}</li>
                    <li class="text-info"><strong>Extra:</strong> ${metrics.extra_matches}</li>
                </ul>
            </div>
        </div>
    `;
    
    verificationMetrics.innerHTML = html;
    verificationContent.style.display = 'block';
    
    // Create verification charts
    createVerificationCharts(metrics);
}

// Create verification charts
function createVerificationCharts(metrics) {
    // Metrics chart (accuracy, precision, recall, F1)
    const metricsCtx = document.getElementById('metricsChart').getContext('2d');
    
    if (charts.metrics) {
        charts.metrics.destroy();
    }
    
    charts.metrics = new Chart(metricsCtx, {
        type: 'bar',
        data: {
            labels: ['Accuracy', 'Precision', 'Recall', 'F1 Score'],
            datasets: [{
                label: 'Score',
                data: [
                    metrics.accuracy * 100,
                    metrics.precision * 100,
                    metrics.recall * 100,
                    metrics.f1_score * 100
                ],
                backgroundColor: [
                    'rgba(40, 167, 69, 0.8)',
                    'rgba(102, 126, 234, 0.8)',
                    'rgba(255, 193, 7, 0.8)',
                    'rgba(220, 53, 69, 0.8)'
                ],
                borderColor: [
                    'rgba(40, 167, 69, 1)',
                    'rgba(102, 126, 234, 1)',
                    'rgba(255, 193, 7, 1)',
                    'rgba(220, 53, 69, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });

    // Detailed metrics chart (correct, incorrect, missed, extra)
    const detailedCtx = document.getElementById('detailedMetricsChart').getContext('2d');
    
    if (charts.detailedMetrics) {
        charts.detailedMetrics.destroy();
    }
    
    charts.detailedMetrics = new Chart(detailedCtx, {
        type: 'doughnut',
        data: {
            labels: ['Correct', 'Incorrect', 'Missed', 'Extra'],
            datasets: [{
                data: [
                    metrics.correct_matches,
                    metrics.incorrect_matches,
                    metrics.missed_matches,
                    metrics.extra_matches
                ],
                backgroundColor: [
                    '#28a745',
                    '#dc3545',
                    '#ffc107',
                    '#17a2b8'
                ],
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

// Clear verification results
function clearVerificationResults() {
    const verificationContent = document.getElementById('verificationContent');
    verificationContent.style.display = 'none';
}

// Download results
function downloadResults() {
    if (currentOutputFile) {
        window.location.href = `/api/download/${currentOutputFile}`;
    }
}

// Update folder information
async function updateFolderInfo() {
    const filmFolder = document.getElementById('filmFolder').value;
    const sceneFolder = document.getElementById('sceneFolder').value;
    const folderInfo = document.getElementById('folderInfo');
    
    if (!filmFolder && !sceneFolder) {
        folderInfo.innerHTML = '<p class="text-muted">Select folders to see information</p>';
        folderInfo.style.display = 'block';
        // Hide photo previews
        document.getElementById('filmPhotosPreview').style.display = 'none';
        document.getElementById('scenePhotosPreview').style.display = 'none';
        return;
    }
    
    // Hide the main folder info area when any folder is selected
    folderInfo.style.display = 'none';
    
    if (filmFolder) {
        try {
            const response = await fetch('/api/validate-folder', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ folder_path: `film-photos/${filmFolder}` })
            });
            const data = await response.json();
            
            if (data.success) {
                // Update film folder title with info
                document.getElementById('filmFolderTitle').innerHTML = `
                    Film Photos: ${filmFolder} <small class="text-muted">(${data.total_images} images)</small>
                `;
                // Load and display film photos
                await loadPhotoPreview('film', filmFolder);
            }
        } catch (error) {
            console.error('Error validating film folder:', error);
        }
    } else {
        // Hide film photos preview if no folder selected
        document.getElementById('filmPhotosPreview').style.display = 'none';
        document.getElementById('filmFolderTitle').textContent = 'Film Photos Preview';
    }
    
    if (sceneFolder) {
        try {
            const response = await fetch('/api/validate-folder', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ folder_path: `scene-info/${sceneFolder}` })
            });
            const data = await response.json();
            
            if (data.success) {
                // Update scene folder title with info
                document.getElementById('sceneFolderTitle').innerHTML = `
                    Scene Photos: ${sceneFolder} <small class="text-muted">(${data.total_images} images)</small>
                `;
                // Load and display scene photos
                await loadPhotoPreview('scene', sceneFolder);
            }
        } catch (error) {
            console.error('Error validating scene folder:', error);
        }
    } else {
        // Hide scene photos preview if no folder selected
        document.getElementById('scenePhotosPreview').style.display = 'none';
        document.getElementById('sceneFolderTitle').textContent = 'Scene Photos Preview';
    }
}

// Load photo preview for a specific folder
async function loadPhotoPreview(folderType, folderName) {
    try {
        const response = await fetch(`/api/images/${folderType}/${folderName}`);
        const data = await response.json();
        
        if (data.success && data.image_files.length > 0) {
            const previewId = folderType === 'film' ? 'filmPhotosPreview' : 'scenePhotosPreview';
            const gridId = folderType === 'film' ? 'filmPhotosGrid' : 'scenePhotosGrid';
            
            // Show the preview section
            document.getElementById(previewId).style.display = 'block';
            
            // Create photo grid
            const grid = document.getElementById(gridId);
            grid.innerHTML = '';
            
            // Display first 50 photos as thumbnails
            const photosToShow = data.image_files.slice(0, 50);
            
            photosToShow.forEach(filename => {
                const img = document.createElement('img');
                img.src = `/${folderType === 'film' ? 'film-photos' : 'scene-info'}/${folderName}/${filename}`;
                img.alt = filename;
                img.className = 'photo-thumbnail';
                img.title = filename;
                
                // Add click handler to select photo for inspection
                img.addEventListener('click', (event) => {
                    selectPhotoForInspection(folderType, filename, event);
                });
                
                grid.appendChild(img);
            });
            
            // Show count if there are more photos
            if (data.image_files.length > 50) {
                const moreText = document.createElement('div');
                moreText.className = 'text-muted text-center mt-2';
                moreText.textContent = `... and ${data.image_files.length - 50} more photos`;
                grid.parentNode.appendChild(moreText);
            }
        }
    } catch (error) {
        console.error(`Error loading ${folderType} photos:`, error);
    }
}

// Select photo for inspection
function selectPhotoForInspection(folderType, filename, event) {
    if (folderType === 'film') {
        document.getElementById('inspectFilmPhoto').value = filename;
    } else {
        document.getElementById('inspectScenePhoto').value = filename;
    }
    
    // Show inspection section if both photos are selected
    const filmPhoto = document.getElementById('inspectFilmPhoto').value;
    const scenePhoto = document.getElementById('inspectScenePhoto').value;
    
    if (filmPhoto && scenePhoto) {
        showInspectionSection();
    }
    
    // Visual feedback - remove previous selections and highlight current
    document.querySelectorAll('.photo-thumbnail.selected').forEach(img => {
        img.classList.remove('selected');
    });
    event.target.classList.add('selected');
}

// Show inspection section
function showInspectionSection() {
    const inspectionSection = document.getElementById('inspectionSection');
    inspectionSection.style.display = 'block';
    
    // Load images for current folders
    loadInspectionImages();
}

// Replace loadInspectionImages with a Promise-based version
function loadInspectionImages() {
    return new Promise(async (resolve) => {
        const filmFolder = document.getElementById('filmFolder').value;
        const sceneFolder = document.getElementById('sceneFolder').value;
        if (!filmFolder || !sceneFolder) {
            alert('Please select both film and scene folders first');
            resolve();
            return;
        }
        currentFilmFolder = filmFolder;
        currentSceneFolder = sceneFolder;
        try {
            // Load film images
            const filmResponse = await fetch(`/api/images/film/${filmFolder}`);
            const filmData = await filmResponse.json();
            if (filmData.success) {
                populateImageSelect('inspectFilmPhoto', filmData.image_files);
            }
            // Load scene images
            const sceneResponse = await fetch(`/api/images/scene/${sceneFolder}`);
            const sceneData = await sceneResponse.json();
            if (sceneData.success) {
                populateImageSelect('inspectScenePhoto', sceneData.image_files);
            }
        } catch (error) {
            console.error('Error loading images:', error);
            alert('Error loading images: ' + error.message);
        }
        resolve();
    });
}

// Populate image select dropdown
function populateImageSelect(selectId, images) {
    const select = document.getElementById(selectId);
    select.innerHTML = '<option value="">Select an image...</option>';
    
    images.forEach(image => {
        const option = document.createElement('option');
        option.value = image;
        option.textContent = image;
        select.appendChild(option);
    });
}

// Inspect selected images
async function inspectImages() {
    const filmPhoto = document.getElementById('inspectFilmPhoto').value;
    const scenePhoto = document.getElementById('inspectScenePhoto').value;
    const maxFeatures = parseInt(document.getElementById('inspectMaxFeatures').value);
    const goodMatchPercent = parseFloat(document.getElementById('inspectGoodMatchPercent').value);
    
    if (!filmPhoto || !scenePhoto) {
        alert('Please select both film and scene photos');
        return;
    }
    
    if (!currentFilmFolder || !currentSceneFolder) {
        alert('Please run a matching first to set up folders');
        return;
    }
    
    try {
        const response = await fetch('/api/inspect-images', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                film_folder: currentFilmFolder,
                scene_folder: currentSceneFolder,
                film_photo: filmPhoto,
                scene_photo: scenePhoto,
                max_features: maxFeatures,
                good_match_percent: goodMatchPercent
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayInspectionResults(data);
        } else {
            alert('Inspection failed: ' + data.error);
        }
    } catch (error) {
        console.error('Inspection error:', error);
        alert('Inspection failed: ' + error.message);
    }
}

// Display inspection results
function displayInspectionResults(data) {
    // Show results section
    document.getElementById('inspectionResults').style.display = 'block';
    // Set the visualization image src
    const filmPhoto = document.getElementById('inspectFilmPhoto').value;
    const scenePhoto = document.getElementById('inspectScenePhoto').value;
    const maxFeatures = document.getElementById('inspectMaxFeatures').value;
    const goodMatchPercent = document.getElementById('inspectGoodMatchPercent').value;
    const img = document.getElementById('visualizationImg');
    img.src = `/api/inspect-visual?film_folder=${encodeURIComponent(currentFilmFolder)}&scene_folder=${encodeURIComponent(currentSceneFolder)}&film_photo=${encodeURIComponent(filmPhoto)}&scene_photo=${encodeURIComponent(scenePhoto)}&max_features=${maxFeatures}&good_match_percent=${goodMatchPercent}`;
    // Optionally update keypoint counts if available in data
    if (data.film_keypoints && document.getElementById('filmKeypointCount'))
        document.getElementById('filmKeypointCount').textContent = data.film_keypoints.length;
    if (data.scene_keypoints && document.getElementById('sceneKeypointCount'))
        document.getElementById('sceneKeypointCount').textContent = data.scene_keypoints.length;
}

// Inspect a matched pair from results
async function inspectMatchedPair(filmPhoto, scenePhoto) {
    if (!currentFilmFolder || !currentSceneFolder) {
        alert('Please run a matching first to set up folders');
        return;
    }
    // Show inspection section
    showInspectionSection();
    // Wait for dropdowns to be populated
    await loadInspectionImages();
    // Set the selected images
    document.getElementById('inspectFilmPhoto').value = filmPhoto;
    document.getElementById('inspectScenePhoto').value = scenePhoto;
    // Immediately trigger the inspection
    await inspectImages();
}

// Download button handler (robust blob-based)
document.addEventListener('DOMContentLoaded', function() {
    const downloadBtn = document.getElementById('downloadVisualBtn');
    if (downloadBtn) {
        downloadBtn.onclick = async function() {
            const img = document.getElementById('visualizationImg');
            if (!img.src) return;
            try {
                const response = await fetch(img.src);
                const blob = await response.blob();
                const url = URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                link.download = 'visualization.png';
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                URL.revokeObjectURL(url);
            } catch (e) {
                alert('Failed to download image.');
            }
        };
    }
});
