# Streamlining Incident Documentation in NOCs

**Problem Statement:**  
Incident documentation in Network Operations Centers (NOCs) is often time-consuming and inconsistent, leading to inefficient knowledge transfer. This project implements an intelligent system monitoring solution with real-time analysis, automated reporting, and collaborative features.

## Features
- **User Authentication System**
  - Secure login and registration
  - Session management
  - User-specific report tracking

- **Intelligent System Monitoring**
  - Real-time system status prediction
  - Comprehensive metric tracking (CPU, Memory, Network, etc.)
  - Automated anomaly detection
  - Status classification (Normal, Warning, Critical)

- **Advanced Reporting**
  - Automated report generation
  - Custom report editing
  - Feedback analysis using Google's Gemini AI
  - Issue status tracking (Resolved/Unresolved)
  - Report voting system with trust scores

- **Interactive Q&A System**
  - AI-powered query system using Gemini Pro
  - Context-aware responses
  - Historical data analysis
  - Trend identification

- **Data Management**
  - SQLite database for persistent storage
  - Historical data tracking
  - Search and filtering capabilities
  - Report deletion and management

## Key Technologies
- **Streamlit:** Web interface and interactive components
- **SQLite:** Database management
- **Google Gemini AI:** Natural language processing and Q&A system
- **Python Libraries:**
  - pandas: Data manipulation and analysis
  - python-dotenv: Environment variable management
  - streamlit: Web application framework

## Prerequisites
- Python 3.8+
- Google API key for Gemini AI
- Required Python packages (see requirements.txt)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/incident-docs-noc.git
   cd incident-docs-noc
   ```

2. Create and configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env and add your Google API key
   GOOGLE_API_KEY=your_api_key_here
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   streamlit run login.py
   ```

## Usage Guide

### Authentication
1. Register a new account or login with existing credentials
2. System maintains session state for authenticated users

### System Monitoring
1. Input system metrics in the Prediction tab
2. View real-time status predictions
3. Generate detailed system reports

### Report Management
1. Edit and customize generated reports
2. Add feedback and observations
3. View AI-generated feedback analysis
4. Vote on reports for quality assessment
5. Filter and search through historical reports

### Q&A System
1. Choose data source (Current Session/Historical/All Data)
2. Ask questions about system status
3. Receive AI-powered responses with context-aware analysis

## Report Trust System
- Reports receive upvotes and downvotes from users
- Trust scores calculated based on voting patterns
- Visual indicators for low-trust reports
- Warning system for potentially unreliable information

## Contributing
We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create your feature branch:
   ```bash
   git checkout -b feature/AmazingFeature
   ```
3. Commit your changes:
   ```bash
   git commit -m 'Add some AmazingFeature'
   ```
4. Push to the branch:
   ```bash
   git push origin feature/AmazingFeature
   ```
5. Open a Pull Request

## Dependencies
```
streamlit>=1.10.0
pandas>=1.4.0
google-generativeai>=0.3.0
python-dotenv>=0.19.0
sqlite3
```

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments
- Google Gemini AI for natural language processing
- Streamlit for the web framework
- Contributors and maintainers
