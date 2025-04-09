import os                                                                                                                                                                                
from google.generativeai import configure, GenerativeModel                                                                                                                               
                                                                                                                                                                                         
def main():                                                                                                                                                                              
    """Queries the Gemini AI model from the command line."""                                                                                                            
                                                                                                                                                                        
    # Configure Generative AI with your API key.                                                                                                                        
    #  Make sure to set the GOOGLE_API_KEY environment variable.                                                                                                        
    api_key = os.environ.get("GOOGLE_API_KEY")                                                                                                                          
    if not api_key:                                                                                                                                                     
        print("Error: GOOGLE_API_KEY environment variable not set.")                                                                                                    
        print("Please set it before running the script.  For example:")                                                                                                 
        print("  export GOOGLE_API_KEY=YOUR_API_KEY")                                                                                                                   
        return                                                                                                                                                          
                                                                                                                                                                        
    configure(api_key=api_key)                                                                                                                                          
                                                                                                                                                                        
    # Define the model.  Using 'gemini-2.0-flash-latest' or 'gemini-pro' might be appropriate, depending on your needs.                                                 
    model_name = 'gemini-2.5-pro-exp-03-25'  #'gemini-2.0-flash' # or "gemini-pro"                                                                                                            
                                                                                                                                                                        
    # Create the model object.                                                                                                                                          
    model = GenerativeModel(model_name)                                                                                                                                 
                                                                                                                                                                        
    # Loop to allow multiple queries.                                                                                                                                   
    while True:                                                                                                                                                         
        try:                                                                                                                                                            
            # Get user input.                                                                                                                                           
            prompt = input("Enter your prompt (or type 'exit' to quit): ")                                                                                              
                                                                                                                                                                        
            # Check for exit condition.                                                                                                                                 
            if prompt.lower() == "exit":                                                                                                                                
                print("Exiting...")                                                                                                                                     
                break                                                                                                                                                   
                                                                                                                                                                        
            # Generate content using the model.                                                                                                                         
            response = model.generate_content(prompt)                                                                                                                   
                                                                                                                                                                        
            # Print the response.                                                                                                                                       
            print("\nResponse:\n", response.text)                                                                                                                       
            print("\n---\n") # Separator for readability                                                                                                                
                                                                                                                                                                        
        except Exception as e:                                                                                                                                          
            print(f"An error occurred: {e}")                                                                                                                            
                                                                                                                                                                        

if __name__ == "__main__":                
    main()   
