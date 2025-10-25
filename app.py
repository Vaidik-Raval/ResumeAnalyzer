from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
import PyPDF2
from docx import Document
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import re
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import logging
import HF_API_KEY #from .env
from huggingface_hub import InferenceClient
import os
hf_token = os.getenv('HF_TOKEN')
# hello test 
# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Hugging Face client

client = InferenceClient(token=HF_API_KEY)

# Download required NLTK data
try:
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('averaged_perceptron_tagger')
    nltk.download('punkt_tab')
    nltk.download('omw-1.4')  # Open Multilingual Wordnet
    logger.info("Successfully downloaded NLTK data")
except Exception as e:
    logger.error(f"Error downloading NLTK data: {str(e)}")
    raise

app = Flask(__name__, static_folder='.')
CORS(app, resources={r"/*": {"origins": "*"}})  # Enable CORS for all routes with all origins
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create uploads directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# Common skills to look for
COMMON_SKILLS = {
    'programming': ['python', 'java', 'javascript', 'c++', 'sql', 'html', 'css', 'php', 'ruby', 'swift', 'kotlin', 'r', 'matlab'],
    'tools': ['git', 'docker', 'kubernetes', 'aws', 'azure', 'jenkins', 'jira', 'confluence', 'slack', 'trello', 'postman'],
    'frameworks': ['react', 'angular', 'vue', 'django', 'flask', 'spring', 'laravel', 'express', 'node.js', 'tensorflow', 'pytorch'],
    'databases': ['mysql', 'postgresql', 'mongodb', 'redis', 'oracle', 'sqlite', 'elasticsearch', 'cassandra'],
    'soft_skills': ['leadership', 'communication', 'problem-solving', 'teamwork', 'project management', 'agile', 'scrum', 'analytical thinking'],
    'methodologies': ['agile', 'scrum', 'waterfall', 'lean', 'six sigma', 'devops', 'ci/cd'],
    'languages': ['english', 'spanish', 'french', 'german', 'chinese', 'japanese', 'korean'],
    'certifications': ['pmp', 'aws', 'azure', 'scrum', 'agile', 'six sigma', 'itil', 'cisco']
}

def extract_text_from_pdf(file_path):
    try:
        text = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            logger.debug(f"PDF Reader created successfully. Number of pages: {len(pdf_reader.pages)}")
            
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text()
                logger.debug(f"Extracted text from page {page_num + 1}")
            
            logger.debug(f"Total text length: {len(text)}")
            return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        raise

def extract_text_from_docx(file_path):
    try:
        doc = Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    except Exception as e:
        logger.error(f"Error extracting text from DOCX: {str(e)}")
        raise

def extract_text(file_path):
    try:
        if file_path.endswith('.pdf'):
            return extract_text_from_pdf(file_path)
        elif file_path.endswith(('.docx', '.doc')):
            return extract_text_from_docx(file_path)
        return ""
    except Exception as e:
        logger.error(f"Error in extract_text: {str(e)}")
        raise

def analyze_resume(text):
    try:
        # Tokenize and clean text
        tokens = word_tokenize(text.lower())
        stop_words = set(stopwords.words('english'))
        
        # Remove stop words and non-alphabetic characters
        cleaned_tokens = [token for token in tokens if token.isalpha() and token not in stop_words]
        
        # Extract skills by category with improved detection
        found_skills = {}
        text_lower = text.lower()
        
        for category, skills in COMMON_SKILLS.items():
            found_skills[category] = []
            for skill in skills:
                # Check for exact matches and variations
                if skill in text_lower or skill.replace('-', ' ') in text_lower or skill.replace(' ', '') in text_lower:
                    found_skills[category].append(skill)
                # Check for common variations (e.g., "js" for "javascript")
                elif skill == 'javascript' and ('js' in text_lower or 'javascript' in text_lower):
                    found_skills[category].append(skill)
                elif skill == 'c++' and ('c++' in text_lower or 'cpp' in text_lower or 'c plus plus' in text_lower):
                    found_skills[category].append(skill)
                elif skill == 'node.js' and ('node.js' in text_lower or 'nodejs' in text_lower or 'node' in text_lower):
                    found_skills[category].append(skill)
        
        # Calculate score based on various factors with weighted scoring
        score = 0
        max_score = 100
        
        # 1. Skills Score (40 points max)
        total_skills = sum(len(skills) for skills in found_skills.values())
        skills_score = min(40, total_skills * 2)  # 2 points per skill, max 40
        
        # 2. Experience Score (25 points max)
        experience_numbers = re.findall(r'\d+', text)
        experience_score = min(25, len(experience_numbers) * 1.5)  # 1.5 points per number, max 25
        
        # 3. Contact Information Score (10 points max)
        contact_info = len(re.findall(r'@|\.com|\.org|\.edu', text))
        contact_score = min(10, contact_info * 2)  # 2 points per contact info, max 10
        
        # 4. Education Score (15 points max)
        education_keywords = ['bachelor', 'master', 'phd', 'degree', 'diploma', 'certification']
        education_count = sum(1 for keyword in education_keywords if keyword in text_lower)
        education_score = min(15, education_count * 3)  # 3 points per education keyword, max 15
        
        # 5. Skills Distribution Score (10 points max)
        categories_with_skills = sum(1 for skills in found_skills.values() if skills)
        distribution_score = min(10, categories_with_skills * 2)  # 2 points per category with skills, max 10
        
        # Calculate total score
        score = skills_score + experience_score + contact_score + education_score + distribution_score
        
        # Generate detailed analysis
        strengths = []
        improvements = []
        recommendations = []
        
        # Skills analysis
        if total_skills > 5:
            strengths.append(f"Strong technical skillset with {total_skills} diverse capabilities")
        else:
            improvements.append("Consider adding more technical skills")
            recommendations.append("Focus on acquiring in-demand technical skills")
        
        # Experience analysis
        if len(experience_numbers) > 5:
            strengths.append("Good experience quantification with measurable achievements")
        else:
            improvements.append("Add more quantifiable achievements")
            recommendations.append("Include specific numbers and metrics in your experience")
        
        # Contact information
        if contact_info > 0:
            strengths.append("Contact information provided")
        else:
            improvements.append("Add contact information")
            recommendations.append("Include your email and professional contact details")
        
        # Education
        if education_count > 0:
            strengths.append("Educational qualifications clearly stated")
        else:
            improvements.append("Add educational background")
            recommendations.append("Include your educational qualifications")
        
        # Skills by category analysis
        skills_analysis = {}
        for category, skills in found_skills.items():
            if skills:
                skills_analysis[category] = {
                    'found': skills,
                    'missing': [skill for skill in COMMON_SKILLS[category] if skill not in skills],
                    'recommendations': []
                }
                
                # Add category-specific recommendations
                if len(skills) < 2:
                    skills_analysis[category]['recommendations'].append(
                        f"Consider adding more {category} skills to strengthen your profile"
                    )
                else:
                    skills_analysis[category]['recommendations'].append(
                        f"Strong {category} skillset with {len(skills)} skills identified"
                    )
        
        # Add overall skills summary
        strengths.append(f"Total skills identified: {total_skills} across {len(found_skills)} categories")
        
        # Add score breakdown to strengths
        strengths.append(f"Score Breakdown:")
        strengths.append(f"- Skills: {skills_score}/40")
        strengths.append(f"- Experience: {experience_score}/25")
        strengths.append(f"- Contact Info: {contact_score}/10")
        strengths.append(f"- Education: {education_score}/15")
        strengths.append(f"- Skills Distribution: {distribution_score}/10")
        
        return {
            'score': score,
            'strengths': strengths,
            'improvements': improvements,
            'recommendations': recommendations,
            'skills_analysis': skills_analysis,
            'experience_count': len(experience_numbers),
            'education_count': education_count,
            'contact_info_present': contact_info > 0,
            'total_skills': total_skills,
            'score_breakdown': {
                'skills': skills_score,
                'experience': experience_score,
                'contact': contact_score,
                'education': education_score,
                'distribution': distribution_score
            }
        }
    except Exception as e:
        logger.error(f"Error in analyze_resume: {str(e)}")
        raise

def get_llm_analysis(text):
    try:
        # Truncate text if too long to avoid token limits
        max_text_length = 2000
        if len(text) > max_text_length:
            text = text[:max_text_length] + "..."
        
        prompt = f"""You are a professional resume analyzer. Please analyze this resume and provide detailed insights:

{text}

Please provide a structured analysis with the following sections:
1. Key Strengths and Unique Selling Points
2. Areas for Improvement
3. Career Trajectory Analysis
4. Industry Fit and Potential Roles
5. Specific Recommendations for Enhancement

Format your response in a clear, professional manner with proper sections and bullet points."""

        # Use a more reliable model
        response = client.text_generation(
            prompt,
            model="meta-llama/Llama-2-7b-chat-hf",  # Using Llama 2 for better reliability
            max_new_tokens=800,
            temperature=0.7,
            top_p=0.95,
            repetition_penalty=1.15,
            do_sample=True,
            return_full_text=False
        )
        
        if not response or len(response.strip()) < 50:
            raise Exception("Generated response was too short or empty")
            
        return response.strip()
    except Exception as e:
        logger.error(f"Error in LLM analysis: {str(e)}")
        # Provide a fallback analysis based on traditional metrics
        return f"""AI Analysis (Fallback):

Key Strengths:
- Technical Skills: {len([skill for skills in COMMON_SKILLS.values() for skill in skills])} skills identified
- Experience: {len(re.findall(r'\d+', text))} quantifiable achievements
- Education: {len(re.findall(r'bachelor|master|phd|degree|diploma|certification', text.lower()))} educational qualifications

Areas for Improvement:
- Consider adding more specific metrics and achievements
- Include more industry-specific skills
- Enhance the presentation of your experience

Career Trajectory:
- Based on your skills and experience, focus on roles that align with your technical expertise
- Consider pursuing relevant certifications to strengthen your profile

Industry Fit:
- Your skillset suggests potential in software development and technical roles
- Consider highlighting industry-specific experience

Recommendations:
1. Add more quantifiable achievements
2. Include industry-specific keywords
3. Highlight relevant certifications
4. Strengthen your professional summary
5. Add more specific technical skills"""

@app.route('/')
def serve_index():
    return send_from_directory('.', 'landing.html')

@app.route('/analyzer')
def serve_analyzer():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        if 'resume' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['resume']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            try:
                logger.debug(f"Processing file: {filename}")
                text = extract_text(file_path)
                logger.debug(f"Extracted text length: {len(text)}")
                
                if not text.strip():
                    return jsonify({'error': 'No text could be extracted from the file'}), 400
                
                # Get both traditional and LLM analysis
                traditional_analysis = analyze_resume(text)
                llm_analysis = get_llm_analysis(text)
                
                # Combine analyses
                combined_analysis = {
                    **traditional_analysis,
                    'llm_analysis': llm_analysis
                }
                
                # Clean up the uploaded file
                os.remove(file_path)
                
                return jsonify(combined_analysis)
            except Exception as e:
                logger.error(f"Error processing file: {str(e)}")
                if os.path.exists(file_path):
                    os.remove(file_path)
                return jsonify({'error': f'Error processing file: {str(e)}'}), 500
        
        return jsonify({'error': 'Invalid file type'}), 400
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'pdf', 'doc', 'docx'}

if __name__ == '__main__':
    app.run(debug=True) 