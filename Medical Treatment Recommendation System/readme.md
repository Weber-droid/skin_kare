# Medical Treatment Recommendation System 🏥

## Overview

An AI-powered medical treatment recommendation system that provides personalized recommendations based on patients' genetic profiles and medical histories.

## Prerequisites

- Python 3.8+
- OpenRouter API Key

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/medical-recommendation-system.git
cd medical-recommendation-system
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install streamlit openai python-dotenv pandas
```

### 4. Configure API Key

1. Create a `.env` file in the project root
2. Add your OpenRouter API key:

```
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

## Running the Application

```bash
streamlit run medical_app.py
```

## Features

- 🧬 Genetic profile analysis
- 📋 Comprehensive medical history tracking
- 🤖 AI-powered treatment recommendations
- 💾 Patient record management

## How to Use

1. Navigate to the "New Patient" tab
2. Enter patient information:
   - Name
   - Age
   - Genetic markers
   - Medical conditions
   - Current medications
   - Allergies
3. Click "Generate Recommendation"
4. View personalized AI-generated treatment suggestions
5. Access patient records in the "View Records" tab

## Important Notes

⚠️ **Disclaimer:**
- This system is for research purposes only
- Always consult healthcare professionals
- Do not use for actual medical decisions

## Troubleshooting

- Ensure OpenRouter API key is valid
- Check internet connection
- Verify all patient fields are filled
- Try different AI models if recommendation fails

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a pull request

## License

MIT License

## Contact

[Your Name]
[Your Email]
