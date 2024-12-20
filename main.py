import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import google.generativeai as genai
import os
from dotenv import load_dotenv
from model import predict

def get_status_color(status):
    return {
        "NORMAL": "green",
        "WARNING": "orange",
        "CRITICAL": "red"
    }.get(status, "gray")

# Load environment variables from .env file
load_dotenv()

def configure_genai():
    api_key = os.getenv('GOOGLE_API_KEY')
    if api_key is None:
        raise ValueError("GOOGLE_API_KEY is not set in the .env file")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-pro")
    return model

def create_database():
    conn = sqlite3.connect('system_reports.db')
    c = conn.cursor()
    
    # Check if the table exists
    c.execute("""SELECT name FROM sqlite_master 
                 WHERE type='table' AND name='reports'""")
    table_exists = c.fetchone() is not None
    
    if not table_exists:
        # Create new table with voting columns
        c.execute('''CREATE TABLE reports
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              username TEXT,
              Date_and_Time TEXT,
              CPU_Utilization INTEGER,
              Memory_Usage INTEGER,
              Bandwidth_Utilization REAL,
              Throughput REAL,
              Latency REAL,
              Jitter REAL,
              Packet_Loss REAL,
              Error_Rates REAL,
              Connection_Establishment_Termination_Times REAL,
              Network_Availability INTEGER,
              Transmission_Delay REAL,
              Grid_Voltage REAL,
              Cooling_Temperature REAL,
              Network_Traffic_Volume REAL,
              System_State TEXT,
              report_text TEXT,
              feedback TEXT,
              upvotes INTEGER DEFAULT 0,
              downvotes INTEGER DEFAULT 0)''')
    else:
        # Check if voting columns exist
        c.execute("PRAGMA table_info(reports)")
        columns = [column[1] for column in c.fetchall()]
        
        if 'upvotes' not in columns:
            c.execute('ALTER TABLE reports ADD COLUMN upvotes INTEGER DEFAULT 0')
        if 'downvotes' not in columns:
            c.execute('ALTER TABLE reports ADD COLUMN downvotes INTEGER DEFAULT 0')
    
    # Create votes tracking table if it doesn't exist
    c.execute("""SELECT name FROM sqlite_master 
                 WHERE type='table' AND name='user_votes'""")
    votes_table_exists = c.fetchone() is not None
    
    if not votes_table_exists:
        c.execute('''CREATE TABLE user_votes
                    (username TEXT,
                     report_id INTEGER,
                     vote_type TEXT,
                     PRIMARY KEY (username, report_id))''')
    
    conn.commit()
    conn.close()
    
def update_vote(report_id, username, vote_type):
    conn = sqlite3.connect('system_reports.db')
    c = conn.cursor()
    
    try:
        # Check if user has already voted
        c.execute("""SELECT vote_type FROM user_votes 
                    WHERE username = ? AND report_id = ?""", 
                    (username, report_id))
        existing_vote = c.fetchone()
        
        if existing_vote:
            old_vote_type = existing_vote[0]
            if old_vote_type == vote_type:
                # User is trying to vote the same way again, remove their vote
                c.execute("""DELETE FROM user_votes 
                           WHERE username = ? AND report_id = ?""",
                           (username, report_id))
                
                if vote_type == 'upvote':
                    c.execute("""UPDATE reports 
                               SET upvotes = upvotes - 1 
                               WHERE id = ?""", (report_id,))
                else:
                    c.execute("""UPDATE reports 
                               SET downvotes = downvotes - 1 
                               WHERE id = ?""", (report_id,))
            else:
                # User is changing their vote
                c.execute("""UPDATE user_votes 
                           SET vote_type = ? 
                           WHERE username = ? AND report_id = ?""",
                           (vote_type, username, report_id))
                
                if vote_type == 'upvote':
                    c.execute("""UPDATE reports 
                               SET upvotes = upvotes + 1, 
                                   downvotes = downvotes - 1 
                               WHERE id = ?""", (report_id,))
                else:
                    c.execute("""UPDATE reports 
                               SET upvotes = upvotes - 1, 
                                   downvotes = downvotes + 1 
                               WHERE id = ?""", (report_id,))
        else:
            # New vote
            c.execute("""INSERT INTO user_votes (username, report_id, vote_type)
                        VALUES (?, ?, ?)""", (username, report_id, vote_type))
            
            if vote_type == 'upvote':
                c.execute("""UPDATE reports 
                           SET upvotes = upvotes + 1 
                           WHERE id = ?""", (report_id,))
            else:
                c.execute("""UPDATE reports 
                           SET downvotes = downvotes + 1 
                           WHERE id = ?""", (report_id,))
        
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    finally:
        conn.close()

def show_reports_tab():
    st.title("Saved Reports")
    reports = get_saved_reports()
    
    # Add search and filter options
    search_term = st.text_input("Search reports by content:")
    status_filter = st.multiselect("Filter by status:", ["Normal", "Abnormal"])
    
    filtered_reports = reports
    if search_term:
        filtered_reports = filtered_reports[
            filtered_reports['report_text'].str.contains(search_term, case=False)]
    if status_filter:
        filtered_reports = filtered_reports[filtered_reports['status'].isin(status_filter)]
    
    # Display reports in an expandable format
    for _, report in filtered_reports.iterrows():
        with st.expander(f"Report from {report['timestamp']} - Status: {report['status']}"):
            st.text(report['report_text'])
            # Safely check for feedback
            try:
                if 'feedback' in report and pd.notna(report['feedback']):
                    st.markdown("### Additional Notes and Feedback")
                    st.text(report['feedback'])
            except KeyError:
                pass  # Skip feedback display if column doesn't exist
            if st.button("Delete Report", key=f"delete_{report['id']}"):
                delete_report(report['id'])
                st.rerun()
def generate_remediation_suggestions(input_data, prediction):
    suggestions = []
    
    if input_data['CPU_Utilization'] >= 80:
        suggestions.append("- Identify and terminate resource-intensive processes\n- Consider upgrading CPU capacity\n- Implement better load balancing")
    
    if input_data['Memory_Usage'] >= 80:
        suggestions.append("- Clear system cache\n- Optimize memory-intensive applications\n- Consider increasing RAM capacity")
    
    if input_data['Error_Rates'] >= 5:
        suggestions.append("- Review system logs for error patterns\n- Update system dependencies\n- Implement error tracking and monitoring")
    
    if input_data['Network_Traffic_Volume'] > 1000:  # Assuming 1000 Mbps threshold
        suggestions.append("- Review network traffic patterns\n- Implement traffic shaping\n- Consider bandwidth upgrade")
    
    if input_data['Cooling_Temperature'] > 30:
        suggestions.append("- Check cooling system functionality\n- Ensure proper ventilation\n- Monitor temperature trends")
    
    if input_data['Bandwidth_Utilization'] > 90:
        suggestions.append("- Analyze bandwidth consumption patterns\n- Implement QoS policies\n- Consider bandwidth optimization techniques")
    
    if input_data['Latency'] > 100:  # Assuming 100ms threshold
        suggestions.append("- Check network connectivity\n- Identify network bottlenecks\n- Optimize network routing")
    
    if input_data['Packet_Loss'] > 2:  # Assuming 2% threshold
        suggestions.append("- Investigate network connectivity issues\n- Check for network congestion\n- Verify network hardware functionality")
    
    if input_data['Jitter'] > 30:  # Assuming 30ms threshold
        suggestions.append("- Monitor network stability\n- Implement jitter buffering\n- Check for network interference")
    
    if input_data['Network_Availability'] < 99:  # Assuming 99% threshold
        suggestions.append("- Review network infrastructure\n- Implement redundancy measures\n- Check for single points of failure")
    
    if input_data['Transmission_Delay'] > 200:  # Assuming 200ms threshold
        suggestions.append("- Optimize data transmission paths\n- Review network topology\n- Consider content delivery optimization")
    
    if input_data['Connection_Establishment_Termination_Times'] > 1000:  # Assuming 1000ms threshold
        suggestions.append("- Check connection pooling settings\n- Optimize connection handling\n- Review connection timeout parameters")
    
    return "\n\n".join(suggestions) if suggestions else "No immediate actions required. Continue regular monitoring."

def generate_report_text(input_data, prediction):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    remediation = generate_remediation_suggestions(input_data, prediction)
    
    # Generate system diagnosis
    issues = []
    if input_data['CPU_Utilization'] >= 80:
        issues.append("High CPU utilization indicating system overload")
    if input_data['Memory_Usage'] >= 80:
        issues.append("Elevated memory usage suggesting resource constraints")
    if input_data['Error_Rates'] >= 5:
        issues.append("High error rates detected indicating potential system issues")
    if input_data['Network_Traffic_Volume'] > 1000:
        issues.append("Excessive network traffic detected suggesting potential network congestion")
    if input_data['Cooling_Temperature'] > 30:
        issues.append("Elevated cooling temperature indicating potential cooling system issues")
    if input_data['Bandwidth_Utilization'] > 90:
        issues.append("High bandwidth utilization indicating potential network bottleneck")
    if input_data['Latency'] > 100:
        issues.append("High network latency detected affecting system performance")
    if input_data['Packet_Loss'] > 2:
        issues.append("Significant packet loss detected affecting network reliability")
    if input_data['Jitter'] > 30:
        issues.append("High jitter levels affecting network stability")
    if input_data['Network_Availability'] < 99:
        issues.append("Reduced network availability affecting system reliability")
    if input_data['Transmission_Delay'] > 200:
        issues.append("High transmission delay affecting data transfer efficiency")
    
    diagnosis = "No significant issues detected." if not issues else "\n- ".join(issues)
    
    report = f"""System Status Report - {timestamp}
    
Overall Status: {prediction}

Network Performance Metrics:
- Bandwidth Utilization: {input_data['Bandwidth_Utilization']}%
- Throughput: {input_data['Throughput']} Mbps
- Latency: {input_data['Latency']} ms
- Jitter: {input_data['Jitter']} ms
- Packet Loss: {input_data['Packet_Loss']}%
- Network Availability: {input_data['Network_Availability']}%

System Resource Metrics:
- CPU Utilization: {input_data['CPU_Utilization']}%
- Memory Usage: {input_data['Memory_Usage']}%
- Grid Voltage: {input_data['Grid_Voltage']} V
- Cooling Temperature: {input_data['Cooling_Temperature']}°C

Network Traffic Analysis:
- Network Traffic Volume: {input_data['Network_Traffic_Volume']} Mbps
- Error Rates: {input_data['Error_Rates']}
- Transmission Delay: {input_data['Transmission_Delay']} ms
- Connection Establishment/Termination Times: {input_data['Connection_Establishment_Termination_Times']} ms

System Diagnosis:
- {diagnosis}

Recommended Actions:
{remediation}
"""
    return report
def save_report_to_db(input_data, prediction, report_text, feedback, model, username):
    """
    Save system report to database with summarized feedback and status
    """
    try:
        # Generate feedback summary and status
        summary_points, issue_status = summarize_feedback(feedback, model)
        
        # Format summary points as a string
        formatted_summary = "\n".join(f"• {point}" for point in summary_points)
        
        # Add status to the feedback
        feedback_with_status = f"Status: {issue_status}\n\nKey Points:\n{formatted_summary}\n\nOriginal Feedback:\n{feedback}"
        
        conn = sqlite3.connect('system_reports.db')
        c = conn.cursor()
        
        # Modify the table to include issue_status if it doesn't exist
        c.execute("PRAGMA table_info(reports)")
        columns = [column[1] for column in c.fetchall()]
        if 'issue_status' not in columns:
            c.execute('ALTER TABLE reports ADD COLUMN issue_status TEXT')
        
        c.execute('''INSERT INTO reports 
                 (username, Date_and_Time, CPU_Utilization, Memory_Usage, Bandwidth_Utilization,
                  Throughput, Latency, Jitter, Packet_Loss, Error_Rates,
                  Connection_Establishment_Termination_Times, Network_Availability,
                  Transmission_Delay, Grid_Voltage, Cooling_Temperature,
                  Network_Traffic_Volume, System_State, report_text, feedback, issue_status)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                 (username,
                  datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                  input_data['CPU_Utilization'],
                  input_data['Memory_Usage'],
                  input_data['Bandwidth_Utilization'],
                  input_data['Throughput'],
                  input_data['Latency'],
                  input_data['Jitter'],
                  input_data['Packet_Loss'],
                  input_data['Error_Rates'],
                  input_data['Connection_Establishment_Termination_Times'],
                  input_data['Network_Availability'],
                  input_data['Transmission_Delay'],
                  input_data['Grid_Voltage'],
                  input_data['Cooling_Temperature'],
                  input_data['Network_Traffic_Volume'],
                  prediction,
                  report_text,
                  feedback_with_status,
                  issue_status))
        
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        raise
    except Exception as e:
        print(f"Error saving report: {e}")
        raise
    finally:
        conn.close()
        
def get_saved_reports():
    conn = sqlite3.connect('system_reports.db')
    reports = pd.read_sql_query("SELECT * FROM reports", conn)
    conn.close()
    return reports

def delete_report(report_id):
    conn = sqlite3.connect('system_reports.db')
    c = conn.cursor()
    c.execute("DELETE FROM reports WHERE id = ?", (report_id,))
    conn.commit()
    conn.close()

def show_prediction_tab():
   st.title("System Status Prediction")
   left_col, right_col = st.columns(2)
   
   with left_col:
       st.header("Input Parameters")
       
       # System Metrics
       grid_voltage = st.number_input("Grid Voltage (V)", min_value=0.0, max_value=500.0, value=220.0)
       cooling_temp = st.number_input("Cooling Temperature (°C)", min_value=0.0, max_value=100.0, value=25.0)
       cpu_utilization = st.slider("CPU Utilization (%)", min_value=0, max_value=100, value=50)
       memory_usage = st.slider("Memory Usage (%)", min_value=0, max_value=100, value=50)

       # Network Metrics
       bandwidth_utilization = st.slider("Bandwidth Utilization (%)", min_value=0, max_value=100, value=50)
       throughput = st.number_input("Throughput (Mbps)", min_value=0.0, max_value=10000.0, value=100.0)
       latency = st.number_input("Latency (ms)", min_value=0.0, max_value=1000.0, value=20.0)
       jitter = st.number_input("Jitter (ms)", min_value=0.0, max_value=100.0, value=5.0)
       packet_loss = st.number_input("Packet Loss (%)", min_value=0.0, max_value=100.0, value=0.1)
       error_rates = st.number_input("Error Rates", min_value=0.0, max_value=100.0, value=0.0)
       
       # Connection Metrics
       connection_times = st.number_input("Connection Times (ms)", min_value=0.0, max_value=5000.0, value=100.0)
       network_availability = st.slider("Network Availability (%)", min_value=0, max_value=100, value=99)
       transmission_delay = st.number_input("Transmission Delay (ms)", min_value=0.0, max_value=1000.0, value=50.0)
       network_traffic_volume = st.number_input("Network Traffic Volume (Mbps)", min_value=0.0, max_value=10000.0, value=100.0)

   with right_col:
       st.header("Prediction Results")
       
       predict_button = st.button("Predict Status")
       if predict_button:
            # Get prediction from model (in correct order)
            prediction = predict(
                CPU_Utilization=cpu_utilization,
                Memory_Usage=memory_usage,
                Bandwidth_Utilization=bandwidth_utilization,
                Throughput=throughput,
                Latency=latency,
                Jitter=jitter,
                Packet_Loss=packet_loss,
                Error_Rates=error_rates,
                Connection_Establishment_Termination_Times=connection_times,
                Network_Availability=network_availability,
                Transmission_Delay=transmission_delay,
                Grid_Voltage=grid_voltage,
                Cooling_Temperature=cooling_temp,
                Network_Traffic_Volume=network_traffic_volume
            )
            
            # Map numerical prediction to status
            status_mapping = {
                0: "NORMAL",
                1: "WARNING",
                2: "CRITICAL"
            }
            status = status_mapping.get(prediction, "UNKNOWN")
            
            # Store current data in session state
            st.session_state.current_input_data = {
                'CPU_Utilization': cpu_utilization,
                'Memory_Usage': memory_usage,
                'Bandwidth_Utilization': bandwidth_utilization,
                'Throughput': throughput,
                'Latency': latency,
                'Jitter': jitter,
                'Packet_Loss': packet_loss,
                'Error_Rates': error_rates,
                'Connection_Establishment_Termination_Times': connection_times,
                'Network_Availability': network_availability,
                'Transmission_Delay': transmission_delay,
                'Grid_Voltage': grid_voltage,
                'Cooling_Temperature': cooling_temp,
                'Network_Traffic_Volume': network_traffic_volume,
                'System_State': status
            }
            st.session_state.current_prediction = status
            
            # Display prediction with color
            st.markdown("### System Status:")
            if status == "NORMAL":
                st.success(status)
            elif status == "WARNING":
                st.warning(status)
            else:
                st.error(status)
            
            st.markdown("### Input Summary:")
            st.dataframe(pd.DataFrame([st.session_state.current_input_data]))
            
            if st.button("Generate Report"):
                st.session_state.current_tab = "Report Generator"
                st.rerun()  

def show_report_generator_tab(username):
    if st.session_state.current_input_data and st.session_state.current_prediction:
        report_text = generate_report_text(st.session_state.current_input_data, 
                                           st.session_state.current_prediction)
        
        edited_report = st.text_area("Edit Report", report_text, height=400)
        
        feedback = st.text_area("Additional Notes and Feedback", 
                                placeholder="Enter any additional observations, comments, or feedback about the system status...",
                                height=150)
        
        if st.button("Save Report"):
            model = configure_genai()
            save_report_to_db(st.session_state.current_input_data,
                              st.session_state.current_prediction,
                              edited_report,
                              feedback,
                              model,
                              username)  # Pass username to save_report_to_db
            st.success("Report saved successfully!")
            
            if feedback:
                summary_points, status = summarize_feedback(feedback, model)
                status_color = "green" if status == "RESOLVED" else "red"
                
                st.markdown(f"""
                <div style="padding: 20px; border-radius: 5px; border: 1px solid {status_color};">
                    <h4 style="color: {status_color};">Status: {status}</h4>
                    <h5>Feedback Summary:</h5>
                    {''.join(f"<p>• {point}</p>" for point in summary_points)}
                </div>
                """, unsafe_allow_html=True)
    else:
        st.warning("Please generate a prediction first!")
        
def summarize_feedback(feedback_text, model):
    """
    Summarize feedback into bullet points and determine issue status using Gemini
    """
    if not feedback_text:
        return [], "UNRESOLVED"
        
    prompt = f"""
    Analyze this system feedback and determine if the issues described are RESOLVED or UNRESOLVED.
    
    Rules for determining status:
    - RESOLVED: Feedback indicates problems have been fixed, solutions implemented, or normal operation restored
    - UNRESOLVED: Feedback describes ongoing issues, problems requiring attention, or pending actions
    
    If there's any uncertainty or ongoing issues mentioned, mark as UNRESOLVED.
    
    Feedback to analyze:
    {feedback_text}
    
    Respond in this exact format:
    STATUS: [RESOLVED/UNRESOLVED]
    REASONING: [Brief explanation of status determination]
    KEY POINTS:
    - [point 1]
    - [point 2]
    etc.
    """
    
    try:
        response = model.generate_content(prompt)
        content = response.text.strip()
        
        # Split content into sections
        sections = content.split('\n')
        
        # Extract status with explicit check
        status_line = next((line for line in sections if line.startswith('STATUS:')), '')
        status = "UNRESOLVED"  # Default to UNRESOLVED
        
        if "STATUS:" in status_line:
            status_value = status_line.split('STATUS:')[1].strip().upper()
            # Only set as RESOLVED if explicitly stated
            if status_value == "RESOLVED":
                status = "RESOLVED"
        
        # Extract bullet points
        points = []
        key_points_started = False
        for line in sections:
            if 'KEY POINTS:' in line:
                key_points_started = True
                continue
            if key_points_started and line.strip().startswith('-'):
                point = line.strip('- ').strip()
                if point:
                    points.append(point)
        
        # If no points were extracted, include the reasoning
        if not points:
            reasoning_line = next((line for line in sections if line.startswith('REASONING:')), '')
            if reasoning_line:
                points = [reasoning_line.split('REASONING:')[1].strip()]
        
        return points, status
        
    except Exception as e:
        st.error(f"Error summarizing feedback: {e}")
        return [feedback_text], "UNRESOLVED"

def preview_feedback_status(feedback, summary_points, status):
    """
    Generate a detailed preview of the feedback analysis
    """
    status_color = "green" if status == "RESOLVED" else "red"
    status_icon = "✓" if status == "RESOLVED" else "!"
    
    return f"""
    <div style="padding: 20px; border-radius: 5px; border: 1px solid {status_color}; background-color: rgba({255 if status == 'RESOLVED' else 255}, {255 if status == 'RESOLVED' else 0}, 0, 0.1);">
        <h4 style="color: {status_color}; margin-top: 0;">
            {status_icon} Status: {status}
        </h4>
        <h5>Analysis Summary:</h5>
        {''.join(f"<p style='margin: 5px 0;'>• {point}</p>" for point in summary_points)}
        <div style="margin-top: 15px; padding-top: 10px; border-top: 1px solid #eee;">
            <details>
                <summary style="cursor: pointer;">Original Feedback</summary>
                <p style="margin-top: 10px; white-space: pre-wrap;">{feedback}</p>
            </details>
        </div>
    </div>
    """

def show_reports_tab(current_username):
    st.title("Saved Reports")
    reports = get_saved_reports()

    # Enhanced search and filter options
    col1, col2, col3 = st.columns(3)
    with col1:
        search_term = st.text_input("Search reports by content:")
    with col2:
        status_filter = st.multiselect("Filter by System State:", ["NORMAL", "WARNING", "CRITICAL"])
    with col3:
        issue_status_filter = st.multiselect("Filter by Issue Status:", ["RESOLVED", "UNRESOLVED"])

    filtered_reports = reports
    if search_term:
        filtered_reports = filtered_reports[
            filtered_reports['report_text'].str.contains(search_term, case=False, na=False)
        ]
    if status_filter:
        filtered_reports = filtered_reports[filtered_reports['System_State'].isin(status_filter)]
    if issue_status_filter:
        filtered_reports = filtered_reports[filtered_reports['issue_status'].isin(issue_status_filter)]

    def summarize_feedback(feedback_text):
        """Convert feedback text into bullet points"""
        sentences = [s.strip() for s in feedback_text.split('.') if s.strip()]
        key_points = []
        for sentence in sentences[:3]:
            point = sentence.strip().replace('\n', ' ')
            if point:
                key_points.append(point)
        return key_points

    def get_trust_warning(trust_score, total_votes):
        """Return appropriate warning message based on trust score and vote count"""
        if total_votes >= 10:  # Significant number of votes
            if trust_score < 30:
                return ("🚫 Highly Untrusted Report", "red", 
                       "This report has been flagged as potentially unreliable by multiple users.")
            elif trust_score < 50:
                return ("⚠️ Low Trust Report", "orange",
                       "This report has received mixed feedback from users.")
        elif total_votes >= 5:  # Moderate number of votes
            if trust_score < 40:
                return ("⚠️ Warning: Low Trust Score", "orange",
                       "This report has received several negative ratings.")
        return None
    
    # Display reports in an expandable format
    for idx, report in filtered_reports.iterrows():
        system_state_color = {
            "NORMAL": "green",
            "WARNING": "orange",
            "CRITICAL": "red"
        }.get(report['System_State'], "gray")
        
        issue_status = report.get('issue_status', 'UNRESOLVED')
        issue_color = "green" if issue_status == "RESOLVED" else "red"
        
        total_votes = report['upvotes'] + report['downvotes']
        trust_score = (report['upvotes'] / total_votes * 100) if total_votes > 0 else 100
        
        if total_votes > 0:
            downvote_percentage = (report['downvotes'] / total_votes) * 100
            is_trustworthy = downvote_percentage <= 50
        else:
            is_trustworthy = True 

        username = report.get('username', 'Unknown User')
        header = (
            f"<div style='display: flex; flex-direction: column; padding: 10px;'>"
            f"<div style='display: flex; justify-content: space-between; align-items: center;'>"
            f"<div>"
            f"<span style='font-weight: bold; margin-right: 15px;'>Report by: {username}</span>"
            f"<span>Date: {report['Date_and_Time']}</span>"
            f"</div>"
            f"<div>"
            f"<span style='color: {system_state_color}; margin-right: 15px;'>System: {report['System_State']}</span>"
            f"<span style='color: {issue_color};'>Status: {issue_status}</span>"
            f"</div>"
            f"</div>"
        )
        
        if total_votes > 0:
            trust_warning = get_trust_warning(trust_score, total_votes)
            if trust_warning:
                warning_icon, warning_color, warning_message = trust_warning
                header += (
                    f"<div style='margin-top: 10px; padding: 8px; background-color: rgba(255,0,0,0.1); "
                    f"border-left: 4px solid {warning_color}; margin-bottom: 10px;'>"
                    f"<span style='color: {warning_color}; font-weight: bold;'>{warning_icon}</span> "
                    f"<span style='color: {warning_color};'>{warning_message}</span>"
                    f"</div>"
                )
        
        header += "</div>"
        
        st.markdown(header, unsafe_allow_html=True)
        
         # Add voting buttons and display vote counts
        col1, col2, col3 = st.columns([1, 1, 8])
        with col1:
            if st.button("👍", key=f"upvote_{report['id']}"):
                if update_vote(report['id'], current_username, 'upvote'):
                    st.rerun()
            st.write(f"{report['upvotes']} upvotes")
            
        with col2:
            if st.button("👎", key=f"downvote_{report['id']}"):
                if update_vote(report['id'], current_username, 'downvote'):
                    st.rerun()
            st.write(f"{report['downvotes']} downvotes")
        
        # Add trust score bar
        if total_votes > 0:
            trust_score = (report['upvotes'] / total_votes) * 100
            with col3:
                st.progress(trust_score / 100)
                st.write(f"Trust Score: {trust_score:.1f}% ({total_votes} votes)")
        
        with st.expander("View Details"):
            # System Metrics Section
            st.markdown("### System Metrics")
            col1, col2 = st.columns(2)
            
            with col1:
                metrics = {
                    "CPU Utilization": f"{report['CPU_Utilization']}%",
                    "Memory Usage": f"{report['Memory_Usage']}%",
                    "Grid Voltage": f"{report['Grid_Voltage']} V",
                    "Cooling Temperature": f"{report['Cooling_Temperature']}°C"
                }
                for label, value in metrics.items():
                    st.markdown(f"**{label}:** {value}")
            
            with col2:
                metrics = {
                    "Network Traffic Volume": f"{report['Network_Traffic_Volume']} Mbps",
                    "Error Rates": f"{report['Error_Rates']}%",
                    "Network Availability": f"{report['Network_Availability']}%"
                }
                for label, value in metrics.items():
                    st.markdown(f"**{label}:** {value}")

            # Network Metrics Section
            st.markdown("### Network Metrics")
            col3, col4 = st.columns(2)
            
            with col3:
                metrics = {
                    "Bandwidth Utilization": f"{report['Bandwidth_Utilization']} Mbps",
                    "Throughput": f"{report['Throughput']} Mbps",
                    "Latency": f"{report['Latency']} ms",
                    "Jitter": f"{report['Jitter']} ms"
                }
                for label, value in metrics.items():
                    st.markdown(f"**{label}:** {value}")
            
            with col4:
                metrics = {
                    "Packet Loss": f"{report['Packet_Loss']}%",
                    "Connection Times": f"{report['Connection_Establishment_Termination_Times']} ms",
                    "Transmission Delay": f"{report['Transmission_Delay']} ms"
                }
                for label, value in metrics.items():
                    st.markdown(f"**{label}:** {value}")

            # Full Report Section
            if report['report_text']:
                st.markdown("### Full Report")
                report_html = f"{report['report_text'].replace(chr(10), '<br>')}"
                st.markdown(report_html, unsafe_allow_html=True)

            # Feedback Section
            if 'feedback' in report and pd.notna(report['feedback']):
                st.markdown("### Feedback Analysis")
                
                original_feedback = report['feedback']
                if 'Original Feedback:' in original_feedback:
                    feedback_parts = original_feedback.split('Original Feedback:')
                    summary_text = feedback_parts[0]
                    original_text = feedback_parts[1] if len(feedback_parts) > 1 else ''
                else:
                    summary_text = original_feedback
                    original_text = ''

                # Generate bullet-point summary
                key_points = summarize_feedback(summary_text)
                
                summary_html = (
                    f"<div style='border-left: 5px solid {issue_color}; padding-left: 15px;'>"
                    "<ul style='margin: 0; padding-left: 20px;'>"
                )
                for point in key_points:
                    summary_html += f"<li>{point}</li>"
                summary_html += "</ul></div>"
                                    
                st.markdown(summary_html, unsafe_allow_html=True)

        # Original Feedback Section (at same level as main expander)
        if 'feedback' in report and pd.notna(report['feedback']):
            with st.expander("View Original Feedback"):
                if original_text:
                    st.markdown(original_text)
                else:
                    st.markdown(original_feedback)
                    
        # Delete button moved here, after the View Original Feedback expander
        if st.button("Delete Report", key=f"delete_{report['id']}", type="secondary"):
            delete_report(report['id'])
            st.success("Report deleted successfully!")
            st.rerun()

        st.markdown("---")  # Add separator between reports
        
def show_qa_tab(model):
    st.title("Q&A System")
    
    # Add option to choose between current or historical data
    data_source = st.radio(
        "Choose data source to query:",
        ["Current Session", "Historical Reports", "All Data"]
    )
    
    user_question = st.text_input("Ask a question about the system status:")
    
    if user_question:
        context_data = ""
        
        if data_source == "Current Session":
            if not st.session_state.current_input_data:
                st.warning("No current session data available. Please generate a prediction first or choose 'Historical Reports'.")
                return
            
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            context_data = f"""Current Session Data:
            Time: {current_time}
            System Status: {st.session_state.current_prediction}
            CPU Utilization: {st.session_state.current_input_data['CPU_Utilization']}%
            Memory Usage: {st.session_state.current_input_data['Memory_Usage']}%
            Bandwidth Utilization: {st.session_state.current_input_data['Bandwidth_Utilization']} Mbps
            Network Traffic Volume: {st.session_state.current_input_data['Network_Traffic_Volume']} GB
            System State: {st.session_state.current_input_data['System_State']}"""
            
        elif data_source == "Historical Reports" or data_source == "All Data":
            # Get historical data from database
            reports = get_saved_reports()
            if reports.empty:
                st.warning("No historical reports found in the database.")
                return
                
            # Format historical data
            historical_context = "\nHistorical Reports:\n"
            for idx, report in reports.iterrows():
                historical_context += f"""
                Report {idx + 1} - {report['Date_and_Time']}:
                System State: {report['System_State']}
                CPU Utilization: {report['CPU_Utilization']}%
                Memory Usage: {report['Memory_Usage']}%
                Bandwidth Utilization: {report['Bandwidth_Utilization']} Mbps
                Network Traffic Volume: {report['Network_Traffic_Volume']} Mbps
                Error Rates: {report['Error_Rates']}%
                Network Availability: {report['Network_Availability']}%
                """
            
            context_data = historical_context
            
            # Add current session data if "All Data" is selected
            if data_source == "All Data" and st.session_state.current_input_data:
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                current_context = f"""
                Current Session Data:
                Time: {current_time}
                System Status: {st.session_state.current_prediction}
                CPU Utilization: {st.session_state.current_input_data['CPU_Utilization']}%
                Memory Usage: {st.session_state.current_input_data['Memory_Usage']}%
                Bandwidth Utilization: {st.session_state.current_input_data['Bandwidth_Utilization']} Mbps
                Network Traffic Volume: {st.session_state.current_input_data['Network_Traffic_Volume']} GB
                System State: {st.session_state.current_input_data['System_State']}"""
                context_data = current_context + "\n" + context_data

        system_context = f"""
        You are a helpful system monitoring assistant. Here is the available system information:

        {context_data}

        The system is considered abnormal if any of these conditions are met:
        - CPU Utilization >= 80%
        - Memory Usage >= 80%
        - Latency >= 200 ms
        - Packet Loss >= 1%
        - Error Rates >= 5%
        - Transmission Delay >= 100 ms
        - Network Availability < 99.9%

        When analyzing trends or comparing data, please consider both historical and current data if available.
        Please provide a natural, conversational response to this question: {user_question}
        
        If asked about trends or patterns, analyze the data across different time periods.
        If asked about specific metrics, provide relevant comparisons when possible.
        If asked about system health, consider both current and historical states to provide context.
        """
        
        try:
            with st.spinner("Analyzing data and generating response..."):
                response = model.generate_content(system_context)
                cleaned_response = response.text.replace('*', '').strip()
                st.markdown("### Answer:")
                st.write(cleaned_response)
                
        except Exception as e:
            st.error(f"Error generating response: {str(e)}")

def get_saved_reports():
    """Helper function to get reports from database"""
    conn = sqlite3.connect('system_reports.db')
    try:
        reports = pd.read_sql_query("SELECT * FROM reports", conn)
        return reports
    except Exception as e:
        st.error(f"Error reading from database: {e}")
        return pd.DataFrame()  # Return empty DataFrame on error
    finally:
        conn.close()

def main(username):
    st.set_page_config(page_title="System Status Predictor", layout="wide")
    
    # Initialize session state
    if 'current_tab' not in st.session_state:
        st.session_state.current_tab = "Prediction"
    if 'current_input_data' not in st.session_state:
        st.session_state.current_input_data = None
    if 'current_prediction' not in st.session_state:
        st.session_state.current_prediction = None
    
    # Initialize database and model
    create_database()
    model = configure_genai()
    
    # Tab selection
    tab_options = ["Prediction", "Report Generator", "Q&A", "View Reports"]
    st.session_state.current_tab = st.radio("Navigation", tab_options, horizontal=True)
    
    # Show appropriate tab
    if st.session_state.current_tab == "Prediction":
        show_prediction_tab()
    elif st.session_state.current_tab == "Report Generator":
        show_report_generator_tab(username)
    elif st.session_state.current_tab == "Q&A":
        show_qa_tab(model)
    elif st.session_state.current_tab == "View Reports":
        show_reports_tab(username)