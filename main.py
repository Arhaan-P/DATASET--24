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
        # Create new table with all columns
      c.execute('''CREATE TABLE reports
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
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
              feedback TEXT)''')
    else:
        # Check if feedback column exists
        c.execute("PRAGMA table_info(reports)")
        columns = [column[1] for column in c.fetchall()]
        
        if 'feedback' not in columns:
            # Add feedback column to existing table
            c.execute('ALTER TABLE reports ADD COLUMN feedback TEXT')
    
    conn.commit()
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
def save_report_to_db(input_data, prediction, report_text, feedback):
    """
    Save system report to database with updated column names.
    
    Parameters:
    input_data (dict): Dictionary containing system metrics
    prediction (str): System state prediction
    report_text (str): Generated report text
    feedback (str): Additional feedback and notes
    """
    try:
        # Connect to SQLite database
        conn = sqlite3.connect('system_reports.db')
        c = conn.cursor()
        
        # Insert data into the reports table
        c.execute('''INSERT INTO reports 
                 (Date_and_Time, CPU_Utilization, Memory_Usage, Bandwidth_Utilization,
                  Throughput, Latency, Jitter, Packet_Loss, Error_Rates,
                  Connection_Establishment_Termination_Times, Network_Availability,
                  Transmission_Delay, Grid_Voltage, Cooling_Temperature,
                  Network_Traffic_Volume, System_State, report_text, feedback)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
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
               feedback))
        
        # Commit the changes and close the connection
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

def show_report_generator_tab():
    st.title("Report Generator")
    if st.session_state.current_input_data and st.session_state.current_prediction:
        report_text = generate_report_text(st.session_state.current_input_data, 
                                        st.session_state.current_prediction)
        
        edited_report = st.text_area("Edit Report", report_text, height=400)
        
        # Add feedback text box
        feedback = st.text_area("Additional Notes and Feedback", 
                              placeholder="Enter any additional observations, comments, or feedback about the system status...",
                              height=150)
        
        if st.button("Save Report"):
            save_report_to_db(st.session_state.current_input_data,
                            st.session_state.current_prediction,
                            edited_report,
                            feedback)
            st.success("Report saved successfully!")
    else:
        st.warning("Please generate a prediction first!")

def show_reports_tab():
    st.title("Saved Reports")
    reports = get_saved_reports()

    # Add search and filter options
    search_term = st.text_input("Search reports by content:")
    status_filter = st.multiselect("Filter by System State:", ["NORMAL", "WARNING", "CRITICAL"])

    filtered_reports = reports
    if search_term:
        filtered_reports = filtered_reports[
            filtered_reports['report_text'].str.contains(search_term, case=False, na=False)
        ]
    if status_filter:
        # Convert filter to match exact system states
        filtered_reports = filtered_reports[filtered_reports['System_State'].isin(status_filter)]

    # Display reports in an expandable format
    for _, report in filtered_reports.iterrows():
        # Color code the expander based on system state
        status_color = {
            "NORMAL": "green",
            "WARNING": "orange",
            "CRITICAL": "red"
        }.get(report['System_State'], "gray")
        
        with st.expander(
            f"Report from {report['Date_and_Time']} - System State: {report['System_State']}"
        ):
            # System Metrics Section
            st.markdown("### System Metrics")
            col1, col2 = st.columns(2)
            
            with col1:
                st.text(f"CPU Utilization: {report['CPU_Utilization']}%")
                st.text(f"Memory Usage: {report['Memory_Usage']}%")
                st.text(f"Grid Voltage: {report['Grid_Voltage']} V")
                st.text(f"Cooling Temperature: {report['Cooling_Temperature']}°C")
            
            with col2:
                st.text(f"Network Traffic Volume: {report['Network_Traffic_Volume']} Mbps")
                st.text(f"Error Rates: {report['Error_Rates']}%")
                st.text(f"Network Availability: {report['Network_Availability']}%")

            # Network Metrics Section
            st.markdown("### Network Metrics")
            col3, col4 = st.columns(2)
            
            with col3:
                st.text(f"Bandwidth Utilization: {report['Bandwidth_Utilization']} Mbps")
                st.text(f"Throughput: {report['Throughput']} Mbps")
                st.text(f"Latency: {report['Latency']} ms")
                st.text(f"Jitter: {report['Jitter']} ms")
            
            with col4:
                st.text(f"Packet Loss: {report['Packet_Loss']}%")
                st.text(f"Connection Times: {report['Connection_Establishment_Termination_Times']} ms")
                st.text(f"Transmission Delay: {report['Transmission_Delay']} ms")

            # Report Text Section
            if report['report_text']:
                st.markdown("### Full Report")
                st.text(report['report_text'])

            # Feedback Section
            if 'feedback' in report and pd.notna(report['feedback']):
                st.markdown("### Additional Feedback")
                st.text(report['feedback'])

            # Delete Button
            if st.button("Delete Report", key=f"delete_{report['id']}"):
                delete_report(report['id'])
                st.rerun()

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

def main():
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
        show_report_generator_tab()
    elif st.session_state.current_tab == "Q&A":
        show_qa_tab(model)
    elif st.session_state.current_tab == "View Reports":
        show_reports_tab()

if __name__ == "__main__":
    main()