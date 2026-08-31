import os
import time

from dotenv import load_dotenv
from openai import APIStatusError, APITimeoutError, NotFoundError, OpenAI

load_dotenv()

#  A generalized api is used.
user_api = os.getenv("API_KEY")
user_url = os.getenv("API_URL")
#  Refactor the storage of prompt from .env (must be ignored) to specific "prompt.md",
#  which can be safely tracked by git.
try:
    with open("prompt.md", "r", encoding="utf-8") as f:
        prompt = f.read()
except FileNotFoundError:
    print("Please load the prompt into <prompt.md>.")

runs = 11
models = [
    "gemini-3-pro-preview",
    "gpt-5",
    "grok-4",
    "claude-opus-4-5-20251101",
]
global_error_message = ""


def make_client(api: str, url: str):
    """
    api: api key.
    url: base url.
    returns: the OpenAI client.
    """

    client = OpenAI(api_key=api, base_url=url)
    print("OpenAI client creation successful.")
    return client


def get_response(model: str, message: str, temperature: float, client) -> str:

    # 6 months ago when I was a Haskell nerd,
    # I would never have thought of writing a function
    # that "polutes" global domain...
    # But, convenience prevails.
    # *Tsoding beatbox*
    global global_error_message

    print(f"Questioning {model}")

    try:
        stream = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": message}],
            stream=False,
            temperature=temperature,
        )
        print(f"{model} answer complete.")
        return stream.choices[0].message.content

    except NotFoundError:
        error_message = "Model not found."
        global_error_message = f"{error_message}"
        return ""
    except APITimeoutError:
        error_message = "API timeout."
        global_error_message = f"{error_message}"
        return ""
    except APIStatusError as api_status_error:
        error = api_status_error.response.json()
        error_message = error.get("error", {}).get("message", "Unknown error")
        print(f"API Status Error: {error_message}")
        global_error_message = f"{error_message}"
        return ""


def main():

    if user_api and user_url and prompt:
        print("Variables loaded.")
    else:
        print(f"user_api: {"True" if user_api else "False"}")
        print(f"user_url: {"True" if user_url else "False"}")
        print(f"system_message: {"True" if prompt else "False"}")
        return None

    current_client = make_client(user_api, user_url)

    for i in range(runs):
        for current_model in models:
            response = get_response(current_model, prompt, 0.0, current_client)
            """
            It occured to me that, if get_response returned a tuple of 
            (response, error_message), the code can be streamlined and 
            the global parameter abolished.
            Maybe feature for later...
            """
            if not response:
                response = f"Encountered problem {global_error_message}, no response."
            with open(f"{current_model}.md", "a", encoding="utf-8") as the_file:
                the_file.write(f"# Run {i} response, Temperature =0.0:\n\n")
                the_file.write(response)
                the_file.write("\n\n")
            print(f"Run {i} for {current_model} complete.")
            time.sleep(5)
    print("Mission complete.")

    return None


if __name__ == "__main__":
    main()
