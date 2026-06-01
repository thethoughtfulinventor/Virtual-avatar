import json
import os


class UserProfile:

    def __init__(self):

        self.file_path = (
            "data/memory/user_profile.json"
        )

        self.data = {}

        self.load()

    def load(self):
    
        if os.path.exists(
        	self.file_path
        ):
        
            try:
            
                with open(
                	self.file_path,
                	 "r"
                ) as f:
                
                    content = f.read().strip()
                    
                    if content:
                    
                        self.data = json.loads(
                        	content
                        )
                        
                    else:
                    
                        self.data = {}
                        
            except Exception:
            
                self.data = {}
                
        else:
        
            self.data = {}   

    def save(self):

        with open(
            self.file_path,
            "w"
        ) as f:

            json.dump(
                self.data,
                f,
                indent=4
            )

    def set_fact(
        self,
        key,
        value
    ):

        self.data[key] = value

        self.save()

    def get_fact(
        self,
        key
    ):

        return self.data.get(key)

    def remove_fact(
        self,
        key
    ):

        if key in self.data:

            del self.data[key]

            self.save()
