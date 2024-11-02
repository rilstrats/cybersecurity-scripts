from typing import Optional


def get_yes_or_no(prompt: str, default_value: Optional[bool] = None) -> bool:
    """True represents yes, False represents no"""

    if default_value == True:
        prompt += " (Y/n): "
    elif default_value == False:
        prompt += " (y/N): "
    else:
        prompt += " (y/n): "

    while True:
        response = input(prompt)

        if len(response) == 0 and default_value:
            return default_value

        response = response.lower()[0]

        if response == "y":
            return True
        
        elif response == "n":
            return False
