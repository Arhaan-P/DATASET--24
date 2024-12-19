import joblib
from sklearn.preprocessing import StandardScaler

def predict(Grid_Voltage, Cooling_Temperature, CPU_Utilization, Memory_Usage, Bandwidth_Utilization,
            Throughput, Latency, Jitter, Packet_Loss, Error_Rates, 
            Connection_Establishment_Termination_Times, Network_Availability, 
            Transmission_Delay, Network_Traffic_Volume):
    # Load the trained model and scaler
    model = joblib.load('noc_new.joblib')
    scaler = StandardScaler()

    # Create a dictionary from the input arguments
    input_data = {
        'Grid_Voltage': Grid_Voltage,
        'Cooling_Temperature': Cooling_Temperature,
        'CPU_Utilization': CPU_Utilization,
        'Memory_Usage': Memory_Usage,
        'Bandwidth_Utilization': Bandwidth_Utilization,
        'Throughput': Throughput,
        'Latency': Latency,
        'Jitter': Jitter,
        'Packet_Loss': Packet_Loss,
        'Error_Rates': Error_Rates,
        'Connection_Establishment_Termination_Times': Connection_Establishment_Termination_Times,
        'Network_Availability': Network_Availability,
        'Transmission_Delay': Transmission_Delay,
        'Network_Traffic_Volume': Network_Traffic_Volume,
    }

    # Convert the input data into a list that matches the order of your features
    input = [
        input_data['Grid_Voltage'],
        input_data['Cooling_Temperature'],
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
        input_data['Network_Traffic_Volume'],
    ]

    # Reshape input for scaling (it should be a 2D array)
    input_reshaped = [input]  # Make it a list of lists

    # Scale the input data
    scaled_input = scaler.fit_transform(input_reshaped)

    # Make a prediction
    prediction = model.predict(scaled_input)

    # Output the prediction
    return prediction[0]  # Will return 'Normal' or 'Abnormal'