document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const analysisSection = document.getElementById('analysisSection');
    const loading = document.getElementById('loading');
    const results = document.getElementById('results');

    // Drag and drop handlers
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = 'var(--hover-color)';
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.style.borderColor = 'var(--header-text-color)';
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = 'var(--header-text-color)';
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFile(files[0]);
        }
    });

    // File input handler
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFile(e.target.files[0]);
        }
    });

    function handleFile(file) {
        if (!isValidFileType(file)) {
            alert('Please upload a PDF or Word document');
            return;
        }

        // Show analysis section and loading
        analysisSection.style.display = 'block';
        loading.style.display = 'block';
        results.style.display = 'none';

        // Create form data
        const formData = new FormData();
        formData.append('resume', file);

        // Send to backend
        fetch('/analyze', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => {
                    throw new Error(err.error || `HTTP error! status: ${response.status}`);
                });
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            displayResults(data);
            loading.style.display = 'none';
            results.style.display = 'block';
        })
        .catch(error => {
            console.error('Error:', error);
            alert(`Error analyzing resume: ${error.message}`);
            loading.style.display = 'none';
        });
    }

    function isValidFileType(file) {
        const validTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
        return validTypes.includes(file.type);
    }

    function displayResults(data) {
        // Update overall score
        document.getElementById('overallScore').textContent = data.score;

        // Update strengths
        const strengthsList = document.getElementById('strengths');
        strengthsList.innerHTML = '';
        data.strengths.forEach(strength => {
            const li = document.createElement('li');
            li.textContent = strength;
            strengthsList.appendChild(li);
        });

        // Update improvements
        const improvementsList = document.getElementById('improvements');
        improvementsList.innerHTML = '';
        data.improvements.forEach(improvement => {
            const li = document.createElement('li');
            li.textContent = improvement;
            improvementsList.appendChild(li);
        });

        // Update skills with categories
        const skillsGrid = document.getElementById('skills');
        skillsGrid.innerHTML = '';
        
        // Add summary section
        const summaryDiv = document.createElement('div');
        summaryDiv.className = 'summary-section';
        summaryDiv.innerHTML = `
            <h3>Resume Summary</h3>
            <p>Total Skills: ${data.total_skills}</p>
            <p>Experience Metrics: ${data.experience_count}</p>
            <p>Education Level: ${data.education_count}</p>
            <p>Contact Info: ${data.contact_info_present ? 'Present' : 'Missing'}</p>
        `;
        skillsGrid.appendChild(summaryDiv);

        // Add skills by category
        Object.entries(data.skills_analysis).forEach(([category, analysis]) => {
            const categoryDiv = document.createElement('div');
            categoryDiv.className = 'category-section';
            categoryDiv.innerHTML = `
                <h3>${category.charAt(0).toUpperCase() + category.slice(1)} Skills</h3>
                <div class="found-skills">
                    <h4>Found Skills:</h4>
                    <div class="skill-tags">
                        ${analysis.found.map(skill => `<span class="skill-item">${skill}</span>`).join('')}
                    </div>
                </div>
                ${analysis.missing.length > 0 ? `
                    <div class="missing-skills">
                        <h4>Recommended Skills:</h4>
                        <div class="skill-tags">
                            ${analysis.missing.slice(0, 3).map(skill => `<span class="skill-item recommended">${skill}</span>`).join('')}
                        </div>
                    </div>
                ` : ''}
                ${analysis.recommendations.length > 0 ? `
                    <div class="recommendations">
                        <p>${analysis.recommendations[0]}</p>
                    </div>
                ` : ''}
            `;
            skillsGrid.appendChild(categoryDiv);
        });

        // Add general recommendations
        if (data.recommendations.length > 0) {
            const recommendationsDiv = document.createElement('div');
            recommendationsDiv.className = 'recommendations-section';
            recommendationsDiv.innerHTML = `
                <h3>General Recommendations</h3>
                <ul>
                    ${data.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                </ul>
            `;
            skillsGrid.appendChild(recommendationsDiv);
        }

        // Add LLM Analysis section
        if (data.llm_analysis) {
            const llmDiv = document.createElement('div');
            llmDiv.className = 'llm-analysis-section';
            llmDiv.innerHTML = `
                <h3>AI-Powered Analysis</h3>
                <div class="llm-content">
                    ${data.llm_analysis.replace(/\n/g, '<br>')}
                </div>
            `;
            skillsGrid.appendChild(llmDiv);
        }
    }

    // Theme toggle functionality
    const themeToggle = document.getElementById('themeToggle');
    const themeIcon = themeToggle.querySelector('.theme-icon');
    const themeText = themeToggle.querySelector('.theme-text');

    // Check for saved theme preference
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeButton(savedTheme);

    themeToggle.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        updateThemeButton(newTheme);
    });

    function updateThemeButton(theme) {
        themeIcon.textContent = theme === 'light' ? '🌙' : '☀️';
        themeText.textContent = theme === 'light' ? 'Dark Mode' : 'Light Mode';
    }
}); 