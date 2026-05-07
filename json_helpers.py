def _try_parse_json(text):
    """Parse JSON from LLM output, handling truncated/malformed responses."""
    import json, re
    
    # Strip thinking tags and markdown fences
    text = re.sub(r"<think.*?</think\s*>", "", text, flags=re.DOTALL).strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    
    # Replace literal newlines with \\n for JSON compatibility
    # (LLMs often put actual newlines inside JSON strings)
    # Strategy: only escape newlines that are NOT part of JSON structure
    lines = text.split('\n')
    processed = []
    for line in lines:
        stripped = line.strip()
        # If line looks like a JSON key-value, keep newline as structural
        if stripped.startswith('"') and ':' in stripped and (stripped.endswith(',') or stripped.endswith('}') or stripped.endswith(']')):
            processed.append('\n' + line)
        else:
            # This is likely content inside a string value — escape it
            if processed:
                processed.append('\\n' + line)
            else:
                processed.append(line)
    text = ''.join(processed)
    
    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Extract JSON object — find matching braces
    depth = 0
    start = -1
    in_string = False
    escape = False
    for i, ch in enumerate(text):
        if escape:
            escape = False
            continue
        if ch == '\\\\':
            escape = True
            continue
        if ch == '"' and not escape:
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == '{':
            if depth == 0:
                start = i
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0 and start >= 0:
                candidate = text[start:i+1]
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    pass
    
    # Truncation recovery: find last complete value and close the object
    # Try to close any open string and any open braces
    if '{' in text:
        # Find where the truncated string starts
        # Work backwards to find the last complete key-value pair
        # Look for pattern: "...", "key": "truncated_value
        # We want to cut at the last complete value
        
        # Simple approach: try progressively shorter truncation points
        for sep in ['},', ']', '",', '"]']:
            last_complete = text.rfind(sep)
            if last_complete > 0:
                candidate = text[:last_complete + 1]
                # Add closing braces
                ob = candidate.count('{') - candidate.count('}')
                oarr = candidate.count('[') - candidate.count(']')
                candidate += ']' * max(0, oarr) + '}' * max(0, ob)
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    continue
    
    # Last resort: extract what we can with regex
    qt_match = re.search(r'"question_text"\s*:\s*"((?:[^"\\]|\\.)*)"', text)
    ca_match = re.search(r'"correct_answer"\s*:\s*"([^"]*)"', text)
    wa_match = re.search(r'"wrong_answers"\s*:\s*\[((?:[^\[\]]|\[(?:[^\[\]]|\[[^\[\]]*\])*\])*)\]', text)
    exp_match = re.search(r'"explanation"\s*:\s*"((?:[^"\\]|\\.)*)"', text)
    
    if qt_match and ca_match and wa_match:
        result = {
            "question_text": qt_match.group(1).replace('\\n', '\n'),
            "correct_answer": ca_match.group(1),
            "wrong_answers": json.loads(wa_match.group(1)) if wa_match else [],
        }
        if exp_match:
            result["explanation"] = exp_match.group(1).replace('\\n', '\n')
        return result
    
    return None
