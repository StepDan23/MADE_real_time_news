"""utility methods"""

async def get_back_response(session, url):
    async with session.get(url=url, raise_for_status=True) as response:
        if response.status == 200:
            return await response.json()
    return Exception


def parse_answer(text, max_length):
    sentences = text.split('.')
    messages = []
    message = ''
    for sentence in sentences:
        if len(message + sentence) < max_length:
            message += sentence
        else:
            messages.append(message)
            message = sentence
    messages.append(sentence + '\n\n')
    return messages