import os
import openai
import ldclient
from ldclient import Context
from ldclient.config import Config
from ldai.client import LDAIClient, AIConfig, ModelConfig, LDMessage, ProviderConfig
from flask import Flask, render_template
from flask import jsonify 
from dotenv import load_dotenv

app = Flask(__name__)

load_dotenv()

LD_CONFIG_KEY = "deepseek-chat"
DEFAULT_CONFIG = {
    "enabled": True,
    "model": {"name": "deepseek-chat"},  
    "messages": [],
}

# Initialize clients
ldclient.set_config(Config(os.getenv("LAUNCHDARKLY_SDK_KEY")))  # Properly configure LaunchDarkly
ld_ai_client = LDAIClient(ldclient.get())  # Get the initialized LD client

# ldclient = os.getenv("LAUNCHDARKLY_SDK_KEY")
openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate(options=None):
   """
   Calls OpenAI's chat completion API to generate some text based on a prompt.
   """
   context = Context.builder('example-user-key').kind('user').name('Sandy').build()

   try:
       ai_config_key = "deepseek-chat"
       default_value = AIConfig(
       enabled=True,
       model=ModelConfig(name='deepseek-chat'),
       messages=[],
    )
       config_value, tracker = ldclient.config(
        ai_config_key,
        context,
        default_value,
    )
       model_name = config_value.model.name
    #    print("CONFIG VALUE: ", config_value)
    #    print("MODEL NAME: ", model_name)
       messages = [] if config_value.messages is None else config_value.messages
       completion = tracker.track_openai_metrics(
            lambda:
                openai_client.chat.completions.create(
                    model=model_name,
                    messages=[message.to_dict() for message in messages],
                )
        )
       response = completion.choices[0].message.content
       print("Success.")
       print("AI Response:", response)
       return response
   except Exception as error:
        print("Error generating AI response:", error)
        return None

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/generate", methods=["GET"])
def generate_text():
    response = generate()
    return jsonify({"text": response})

if __name__ == "__main__":
    if not ldclient:
        print("*** Please set the LAUNCHDARKLY_SDK_KEY env first")
        exit()

    ldclient.set_config(Config(ldclient))

    if not ldclient.get().is_initialized():
        print("*** SDK failed to initialize. Please check your internet connection and SDK credential for any typo.")
        exit()

    print("*** SDK successfully initialized")
    
    try:
        app.run(debug=True)
        Event().wait()
    except KeyboardInterrupt:
        pass