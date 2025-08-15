from configs.zoekt import SearchConfig
import requests
from urllib3.exceptions import NewConnectionError
from requests.exceptions import ConnectionError, Timeout , RequestException
import  json
import time
class ZoektSearchRequester:
    """
    A class to handle search requests to Zoekt.
    """
    
    def __init__(self, config: SearchConfig):
        self.config = config

    def zoekt_search_request(
                        self,
                        query: str,
                       ) -> dict:
        """
        Make a request to the zoekt search API with error handling and retry logic.
        
        Args:
            query: Search query string
            num_context_lines: Number of context lines to include
            max_results: Maximum number of results to return
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
        
        Returns:
            Dict containing search results or empty result on failure
        """
        if query is None or query.strip() == "":
            print("Empty query provided. Returning empty result.")
            return {"Result": {"Files": [], "FileCount": 0}}
        
        url = self.config.zoekt_url
        payload = json.dumps({
            "Q": query,
            "Opts": {
                "NumContextLines": self.config.num_context_lines,
                "MaxResults": self.config.max_results,
            }
        })
        headers = {
            'Content-Type': 'application/json'
        }

        for attempt in range(self.config.max_retries + 1):
            try:
                response = requests.request("POST", url, headers=headers, data=payload, timeout=30)
                
                # Check if response is successful
                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"HTTP {response.status_code} error: {response.text}")
                    if attempt < self.config.max_retries:
                        print(f"Retrying in {self.config.retry_delay} seconds... (attempt {attempt + 1}/{self.config.max_retries})")
                        time.sleep(self.config.retry_delay)
                        continue
                    else:
                        print("Max retries reached. Returning empty result.")
                        return {"Result": {"Files": [], "FileCount": 0}}
                        
            except (ConnectionError, NewConnectionError) as e:
                print(f"Connection error on attempt {attempt + 1}: {e}")
                if attempt < self.config.max_retries:
                    print(f"Zoekt service might be down. Retrying in {self.config.retry_delay} seconds...")
                    time.sleep(self.config.retry_delay)
                else:
                    print("Failed to connect to Zoekt service after all retries.")
                    print("Please check if Zoekt is running on http://localhost:6070")
                    return {"Result": {"Files": [], "FileCount": 0}}
                    
            except Timeout as e:
                print(f"Request timeout on attempt {attempt + 1}: {e}")
                if attempt < self.config.max_retries:
                    print(f"Retrying in {self.config.retry_delay} seconds...")
                    time.sleep(self.config.retry_delay)
                else:
                    print("Request timed out after all retries.")
                    return {"Result": {"Files": [], "FileCount": 0}}
                    
            except RequestException as e:
                print(f"Request error on attempt {attempt + 1}: {e}")
                if attempt < self.config.max_retries:
                    print(f"Retrying in {self.config.retry_delay} seconds...")
                    time.sleep(self.config.retry_delay)
                else:
                    print("Request failed after all retries.")
                    return {"Result": {"Files": [], "FileCount": 0}}
                    
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
                print(f"Response content: {response.text if 'response' in locals() else 'No response'}")
                return {"Result": {"Files": [], "FileCount": 0}}
                
            except Exception as e:
                print(f"Unexpected error: {e}")
                return {"Result": {"Files": [], "FileCount": 0}}
        
        # This should never be reached, but just in case
        return {"Result": {"Files": [], "FileCount": 0}}


    