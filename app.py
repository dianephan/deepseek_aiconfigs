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

# Initialize clients
ldclient.set_config(Config(os.getenv("LAUNCHDARKLY_SDK_KEY")))  
ld_ai_client = LDAIClient(ldclient.get())  

openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# need to used openrouter to run deepseek ai for free 
client = openai.OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=os.getenv("OPENROUTER_API_KEY"),
)

def generate(options=None):
    context = Context.builder('example-user-key').kind('user').name('Sandy').build()

    # name of ai configs projects name
    ai_config_key = "quickdeepseek"
    default_value = AIConfig(
        enabled=True,
        model=ModelConfig(name='deepseek-chat'),
        messages=[],
    )
    config_value, tracker = ld_ai_client.config(
        ai_config_key,
        context,
        default_value,
)
    model_name = config_value.model.name
    print("CONFIG VALUE: ", config_value)
    print("MODEL NAME: ", model_name)
    messages = [] if config_value.messages is None else config_value.messages
    messages_dict=[message.to_dict() for message in messages]

    completion = client.chat.completions.create(
            # deepseek chat is not a valid model. have to change to deepseek/deepseek-r1:free from router
            model="deepseek/deepseek-r1:free",
            messages=messages_dict,
        )
    track_success = tracker.track_success()
    print(completion.choices[0].message.content) 

    print("Successful AI Response:", completion)
    return completion


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/generate", methods=["GET"])
def generate_text():
    response = generate()
    # return jsonify({"text": response})
    return response

if __name__ == "__main__":
    if not ldclient:
        print("*** Please set the LAUNCHDARKLY_SDK_KEY env first")
        exit()

    ldclient.set_config(Config(ldclient))

    if not ldclient.get().is_initialized():
        print("*** SDK failed to initialize. Please check your internet connection and SDK credential for any typo.")
        exit()

    print("*** SDK successfully initialized")

    generate()
    
    try:
        app.run(debug=True)
    except KeyboardInterrupt:
        pass