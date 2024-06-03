import os
import requests
import time
import json
import config
from flask import Flask, render_template, request, jsonify, session
from openai import OpenAI
from json.decoder import JSONDecodeError


OPENAI_API_KEY = config.API_KEY
FLASK_SECRET_KEY = config.FLASK_SECRET_KEY  # Secret key for Flask application


# Set up for using OpenAI APIs
# Note - comment out the line below to avoid sending repeated API calls
client = OpenAI(api_key=OPENAI_API_KEY)

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY


# Store the filenames for images generated with Dall E and associated prompts in JSON file
def save_dalle_prompt_with_image(prompt, revised_prompt=None, image_file_path=None):
    f_path = os.path.join(app.static_folder, 'data', 'dalle_prompts_images.json')
    os.makedirs(os.path.dirname(f_path), exist_ok=True)

    data = []
    try:
        with open(f_path, 'r') as file:
            try:
                data = json.load(file)  # Load the data
            except json.JSONDecodeError:
                pass
    except FileNotFoundError:
        pass

    # Save new_entry as dict
    new_entry = {
        "prompt": prompt,
        "revised_prompt": revised_prompt,
    }

    if image_file_path:
        new_entry["image_file_path"] = image_file_path

    data.append(new_entry)

    with open(f_path, 'w') as file:
        json.dump(data, file, indent=4)


# Get the most recently saved prompt and image
def get_dalle_prompt_with_image():
    f_path = os.path.join(app.static_folder, 'data', 'dalle_prompts_images.json')
    try:
        with open(f_path, 'r') as file:
            data = json.load(file)
            if data:
                return data[-1]  # Return the last entry
    except FileNotFoundError:
        return {}
    return {}


# Get all the prompts and images
def get_all_dalle_prompts_with_images():
    f_path = os.path.join(app.static_folder, 'data', 'dalle_prompts_images.json')
    try:
        with open(f_path, 'r') as file:
            try:
                data = json.load(file)
                return data
            except JSONDecodeError:
                return []
    except FileNotFoundError:
        return []


# Save character descriptions to JSON file
def save_character_description(character_name, description):
    f_path = os.path.join(app.static_folder, 'data', 'character_descriptions.json')

    os.makedirs(os.path.dirname(f_path), exist_ok=True)

    descriptions = {}
    try:
        with open(f_path, 'r') as file:
            try:
                descriptions = json.load(file)
            except JSONDecodeError:
                pass
    except FileNotFoundError:
        pass

    descriptions[character_name] = description

    with open(f_path, 'w') as file:
        json.dump(descriptions, file, indent=4)


# Retrieve the description from the JSON file and call this function to display it on the page
def get_character_description(character_name):
    file_path = os.path.join(app.static_folder, 'data', 'character_descriptions.json')
    try:
        with open(file_path, 'r') as file:
            descriptions = json.load(file)
            return descriptions.get(character_name, "")
    except FileNotFoundError:
        return ""


# Save the messages sent to GPT-4 for creating prompts with character consistency
def save_character_messages(character_name, new_msgs):
    f_path = os.path.join(app.static_folder, 'data', 'character_messages.json')
    os.makedirs(os.path.dirname(f_path), exist_ok=True)
    try:
        with open(f_path, 'r') as file:
            messages_dict = json.load(file)
    except (FileNotFoundError, JSONDecodeError):
        messages_dict = {}

    character_messages = messages_dict.get(character_name, [])
    character_messages.extend(new_msgs)
    character_messages = character_messages[-10:]
    messages_dict[character_name] = character_messages

    with open(f_path, 'w') as file:
        json.dump(messages_dict, file, indent=4)


def process_plot_ideas(text):
    plot_ideas = []
    lines = text.strip().split('\n')
    idea_dict = {}

    for line in lines:
        if line.startswith('Scene title:'):
            if idea_dict.get('title') and idea_dict.get('description'):
                plot_ideas.append(idea_dict)
                idea_dict = {}
            idea_dict['title'] = line.replace('Scene title:', '').strip()
        elif line.startswith('Scene description:'):
            idea_dict['description'] = line.replace('Scene description:', '').strip()

    if idea_dict.get('title') and idea_dict.get('description'):
        plot_ideas.append(idea_dict)

    return plot_ideas


@app.route("/")
def home():
    return render_template('index.html')


@app.route('/storyboard')
def storyboard():
    return render_template('storyboard.html')


# Build storyboard
@app.route("/process_storyboard", methods=['GET', 'POST'])
def process_storyboard():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    form_action = data.get('form_action')
    genre = data.get('genre')
    theme = data.get('themes')
    setting = data.get('setting')
    premise = data.get('premise')
    storyboard_data = data.get('storyboard')

    if form_action == 'generate_ideas':
        # Construct prompt using form data
        prompt_sections = []

        if genre:
            prompt_sections.append(f"Genre: {genre}")

        if theme:
            prompt_sections.append(f"Theme: {theme}")

        if setting:
            prompt_sections.append(f"Setting: {setting}")

        if premise:
            prompt_sections.append(f"Premise: {premise}")

        prompt_info = "\n".join(section for section in prompt_sections if section)

        print(f"Here is the information the user submitted for plot ideas generation: {prompt_info}")  # Debugging

        storyboard_scenes = "; ".join([scene['description'] for scene in storyboard_data])
        print(f"Here are the storyboard scenes: {storyboard_scenes}")  # Debugging

        plot_system_msg = ("Generate creative and coherent next scenes for a story based on the provided background "
                           "and current scenes. Ensure the scenes are relevant, unique, and build upon the existing "
                           "storyline, taking into account the genre, themes, setting, and character dynamics.")

        user_prompt = (
            f"Based on the current scenes described below, generate two different, unique, detailed suggestions for the next scene "
            f"that logically follows in the story. Include potential plot developments and character actions that fit "
            f"with the established genre, themes, and setting.\n\n"
        )

        if storyboard_scenes != "" or prompt_info != "":
            if storyboard_scenes != "":
                user_prompt += f"Current scenes: {storyboard_scenes}\n\n"

            if prompt_info != "":
                user_prompt += f"Additional information: {prompt_info}\n\n"

            user_prompt += ("For each scene suggestion, format the response as follows:\nScene title: {Title of the "
                            "next scene}\n\nScene description: {80 words long detailed description of the next scene, "
                            "focusing on actions, dialogues, or events that should occur next.}\n\n")

            plot_prompt_response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": plot_system_msg
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    }
                ],
                temperature=0.7,  # ideal temperature for creative but relevant suggestions
                max_tokens=1512,  # increase in max_tokens to account for longer prompt containing more storyboard content - NOTE: would need to make a prior prompt to GPT-4 to summarize storyboard content if there is too much of it
                top_p=1,
                frequency_penalty=0.2,  # slight increase in frequency_penalty to encourage model to use more varied vocabulary
                presence_penalty=0
            )

            # Generate TWO DIFFERENT UNIQUE plot ideas, parse them, and display them on the page

            plot_ideas_response = plot_prompt_response.choices[0].message.content
            print(plot_ideas_response)  # Debugging

            parsed_ideas = process_plot_ideas(plot_ideas_response)
            print(f"HERE ARE THE PARSED PLOT IDEAS: {parsed_ideas}")  # Debugging

            # Generate an image to accompany the plot idea
            for idea in parsed_ideas:
                image_prompt = f"Create an image that illustrates this scene: {idea['description']}"
                try:
                    # Generate the image using DALL-E
                    dalle_response = client.images.generate(
                        model="dall-e-3",
                        prompt=image_prompt,
                        size="1024x1024",
                        quality="standard",
                        n=1,
                        style="vivid",
                        response_format="url",
                    )
                    idea['image_url'] = dalle_response.data[0].url

                    print(f"Image was successfully created for this plot idea: {idea['description']}")  # Debugging
                    print(f"Link to the image: {idea['image_url']}")  # Debugging
                except Exception as e:
                    print(f"Error generating image for idea {idea['title']}: {e}")
                    idea['image_url'] = "Error generating image"

            print(f"Here are the updated parsed ideas which should include the image URLs: {parsed_ideas}")  # Debugging
            return jsonify({'plotIdeas': parsed_ideas})
        else:
            # Tell the user to fill out the form OR the storyboard if they click generate ideas button without doing so
            return jsonify(
                {'error': 'Please add content to the storyboard or fill out the form to generate ideas.'}), 400


    return jsonify({'error': 'Please try again later.'}), 400


# Generate images
@app.route("/generate_images", methods=['GET', 'POST'])
def generate_images():
    # Avoid errors by declaring these variables
    recent_prompt = ""
    character_description = ""

    # Get the form data that the user enters - not all data is required so some variables might be blank
    if request.method == 'POST':
        # Check which button was clicked
        form_action = request.form.get('form_action')

        if form_action == 'create_character':
            # Collect form data
            character_name = request.form.get('character-name')
            session['character_name'] = character_name  # Store in flask session to use for image preferences generation
            gender = request.form.get('character-gender')
            height = request.form.get('character-height')
            ethnicity = request.form.get('character-ethnicity')
            age = request.form.get('character-age')
            hair_style = request.form.get('character-hair')
            eyes = request.form.get('character-eyes')
            clothing = request.form.get('clothing')
            accessories = request.form.get('accessories')
            personality = request.form.get('personality')
            other_features = request.form.get('other-features')

            # Construct prompt for GPT 4 using form data
            character_info = f"{character_name}, a "  # Required field

            # Check if the variable exists before using it in the prompt
            if height:
                character_info += f"{height}, "

            if ethnicity:
                character_info += f"{ethnicity}, "

            character_info += f"{age}-year-old "  # Required field
            character_info += f"{gender} "  # Required field

            if hair_style:
                character_info += f"with {hair_style} "

            if eyes:
                character_info += f"and {eyes} eyes, "

            if clothing:
                character_info += f"is wearing {clothing} "

            if accessories:
                character_info += f"with {accessories}. "

            if personality:
                character_info += f"They have a {personality} personality. "

            if other_features:
                character_info += f"They have other features such as: {other_features}. "

            print(character_info)  # Debugging

            # Make API call
            character_info_system_message = ("You are assisting in generating detailed prompts for creating images "
                                             "with DALL·E 3.")

            character_info_response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": character_info_system_message,
                    },
                    {
                        "role": "user",
                        "content": f"Use these details to generate an 70 word description of a character that I can "
                                   f"use to create an image with Dall E:\n\n{character_info}\n\nIf any of the "
                                   f"following details are missing from the information that is provided, "
                                   f"edit the character description to include this information: height, ethnicity, "
                                   f"hair style (including hair color and length), eye color, eye shape, clothing, "
                                   f"personality, and accessories. Make sure the character description is specific "
                                   f"and unique."
                    }
                ],
                temperature=1,
                max_tokens=256,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
            )

            character_prompt = character_info_response.choices[0].message.content
            print(f"Here is the character description generated by GPT: {character_prompt}")  # Debugging

            # Save character_prompt to JSON file
            save_character_description(character_name, character_prompt)

            # Display result on page (THIS IS NOT NEEDED ANY LONGER)
            # character_description = character_prompt

            # Store the variable in Flask session to access later and display result on page
            session['character_description'] = character_prompt

        elif form_action == 'create_img_prompt':
            #  Process the form data for the Create Scene tab
            char_consistency = request.form.get('char-consistency')
            regular_prompt = request.form.get('regular-prompt')
            negative_prompt = request.form.get('negative-prompt')
            photo_angles = request.form.getlist('angles[]')

            location = request.form.get('location')
            time_period = request.form.get('time-period')
            lighting = request.form.get('lighting')

            preferred_styles = request.form.getlist('styles[]')
            color_palette = request.form.get('color-palette')
            genre = request.form.get('genre')
            mood = request.form.get('mood')

            demeanour = request.form.get('demeanour')
            expression = request.form.get('expression')

            candid_shot = request.form.get('candid-shot')

            # Make the unrefined prompt
            prompt_details = f""

            if negative_prompt:
                prompt_details += f"Avoid including: {negative_prompt}\n\n"

            if photo_angles:
                prompt_details += f"Use the following photo angle(s): {', '.join(photo_angles)}.\n\n"

            if location:
                prompt_details += f"The character is in a {location}.\n\n"

            if time_period:
                prompt_details += f"This is during the {time_period}.\n\n"

            if lighting:
                prompt_details += f"The lighting is {lighting}.\n\n"

            if preferred_styles:
                prompt_details += f"Preferred styles: {', '.join(preferred_styles)}.\n\n"

            if color_palette:
                prompt_details += f"The color palette is: {color_palette}.\n\n"

            if genre:
                prompt_details += f"The genre is: {genre}.\n\n"

            if mood:
                prompt_details += f"The mood is: {mood}.\n\n"

            if demeanour:
                prompt_details += f"The character displays a {demeanour} demeanour.\n\n"

            if expression:
                prompt_details += f"The character has a {expression} expression.\n\n"

            if candid_shot == "yes":
                prompt_details += ("Create an image capturing a purely candid moment, where the subject is completely "
                                   "unaware of the camera. Focus on genuine, spontaneous, expressions and actions.\n\n")
            else:
                prompt_details += ("The character(s) in the image should be posed deliberately and looking directly at "
                                   "the viewer.\n\n")


            char_description = get_character_description(session.get('character_name'))


            # If user wants consistent character art, use separate system_message and append character description
            # when prompting gpt-4
            if char_consistency == "yes":

                # Check whether the first prompt has been submitted to GPT-4 by getting all the prompts from the JSON file
                char_name = session.get('character_name')
                f_path = os.path.join(app.static_folder, 'data', 'character_messages.json')

                try:
                    with open(f_path, 'r') as file:
                        all_messages = json.load(file)
                except (FileNotFoundError, JSONDecodeError):
                    all_messages = {}

                character_messages = all_messages.get(char_name, [])

                # Use one type of prompt for generating the first character image and subsequent prompts will build on the previous prompt

                image_prompt_response = {}

                if not character_messages:
                    # Submit first prompt for generating images for this character
                    system_message = (
                        "You are assisting in generating detailed prompts for creating images with DALL·E 3. "
                        "Ensure the character's appearance is consistent across various scenes.")
                    first_system_message = {
                        "role": "system",
                        "content": system_message,
                    }
                    first_user_message = {
                        "role": "user",
                        "content": f"Refine this prompt for an image: {regular_prompt}\n\nAdd the following details "
                                   f"about the image: {prompt_details} Use this character description: "
                                   f"{char_description}\n\nMake sure that the resulting prompt is under "
                                   f"200 words long and begins with 'Create a high-resolution, detailed, image'"
                    }

                    image_prompt_response = client.chat.completions.create(
                        model="gpt-4",
                        messages=[
                            first_system_message,
                            first_user_message
                        ],
                        temperature=1,
                        max_tokens=256,
                        top_p=1,
                        frequency_penalty=0,
                        presence_penalty=0
                    )


                    new_messages = [
                        first_system_message,
                        first_user_message
                    ]

                    save_character_messages(char_name, new_messages)
                else:
                    standard_user_msg = {
                        "role": "user",
                        "content": ("Adapt the user's previous prompt to generate a new image based on this prompt "
                                         f"and make sure the character's appearance remains consistent: {regular_prompt}"
                                         f"\n\nEdit the prompt by adding the following details about the image:{prompt_details} "
                                         f"Use details from this character description to make sure their appearance "
                                         f"remains consistent in the image: {char_description}")
                        }

                    updated_char_messages = character_messages

                    updated_char_messages.append(standard_user_msg)

                    image_prompt_response = client.chat.completions.create(
                        model="gpt-4",
                        messages=updated_char_messages,
                        temperature=1,
                        max_tokens=256,
                        top_p=1,
                        frequency_penalty=0,
                        presence_penalty=0
                    )

                    new_messages = [
                        standard_user_msg
                    ]

                    save_character_messages(char_name, new_messages)

                assistant_response = {
                    "role": "assistant",
                    "content": image_prompt_response.choices[0].message.content
                }

                new_messages = [
                    assistant_response
                ]
                save_character_messages(char_name, new_messages)

                edited_image_prompt = image_prompt_response.choices[0].message.content

                dall_e_prompt = f"Create an image using the request without modifications: {edited_image_prompt}"

                # Save the full prompt to JSON file
                save_dalle_prompt_with_image(dall_e_prompt)

                # Get the most recent prompt saved to show user
                recent_prompt = f"{edited_image_prompt}"
            else:
                # Create prompt for image generation *WITHOUT* character consistency

                regular_prompt_response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are assisting in generating detailed prompts for creating images with DALL·E 3."
                        },
                        {
                            "role": "user",
                            "content": f"Refine this prompt for an image: {regular_prompt}\n\nAdd the following details "
                                       f"about the image: {prompt_details}\n\nMake sure that the resulting prompt is "
                                       f"under 200 words long and begins with 'Create a high-resolution, detailed, image'"
                        }
                    ],
                    temperature=1,
                    max_tokens=256,
                    top_p=1,
                    frequency_penalty=0,
                    presence_penalty=0
                )

                regular_dalle_prompt = regular_prompt_response.choices[0].message.content

                # Save the full prompt to JSON file
                save_dalle_prompt_with_image(regular_dalle_prompt)

                # Get the most recent prompt saved to show user
                recent_prompt = regular_dalle_prompt

        elif form_action == 'generate_image':
            dall_e_prompt = get_dalle_prompt_with_image()['prompt']

            # Generate image with Dall E 3
            dalle_response = client.images.generate(
                model="dall-e-3",
                prompt=dall_e_prompt,
                size="1024x1024",
                quality="standard",
                n=1,
                style="vivid",
                response_format="url",
            )

            image_url = dalle_response.data[0].url

            revised_prompt = dalle_response.data[0].revised_prompt

            # Save generated image to /static/img in this flask application
            img_folder = os.path.join(app.static_folder, 'img')  # Folder for saving images
            if not os.path.exists(img_folder):
                os.makedirs(img_folder)

            img_response = requests.get(image_url)

            # Create a filename using the first 20 characters from the prompt combined with timestamp
            clean_prompt = ''.join(char for char in dall_e_prompt if char.isalnum() or char in (' ', '_')).rstrip()
            converted_prompt = clean_prompt[:20].replace(' ', '_')  # Convert spaces to underscores
            timestamp = int(time.time())
            img_filename = f"{converted_prompt}_{timestamp}.jpg"
            print(f"Here is the image's filename: {img_filename}.")  # For debugging

            if img_response.status_code == 200:
                img_path = os.path.join(img_folder, img_filename)
                with open(img_path, "wb") as file:
                    file.write(img_response.content)
                #  Save the prompt, revised prompt, and image pair to JSON file
                relative_img_path = os.path.join('img', img_filename)
                print(f"Here is the relative image path where the image is saved: {relative_img_path}")
                save_dalle_prompt_with_image(dall_e_prompt, revised_prompt, relative_img_path)

    else:
        # Get the description for the character
        character_name = request.args.get('character-name')
        if character_name:
            character_description = get_character_description(character_name)

    # Display (REVISED) prompt + generated image pairs on page
    prompt_img_pairs = get_all_dalle_prompts_with_images()  # Get all pairs
    character_description = session.get('character_description', '')  # Get the description from flask session
    return render_template("image_generation.html", prompt_img_pairs=prompt_img_pairs,
                           character_description=character_description, recent_prompt=recent_prompt)


# if __name__ == '__main__':
#     app.run(debug=True)


# The app was giving me a 403 error and would not run with the default 5000 port
if __name__ == "__main__":
    app.run(port=8000, debug=True)
