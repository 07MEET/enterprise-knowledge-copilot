import time


def call_with_retry(func, *args, max_retries=6, initial_delay=2.0, **kwargs):
    """
    Execute an API function with exponential backoff on rate limits (429) or server overload (503).
    """
    delay = initial_delay
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            err_msg = str(e)
            # Catch rate limits (429) or temporary server overload (503)
            is_retryable = (
                "429" in err_msg
                or "503" in err_msg
                or "UNAVAILABLE" in err_msg.upper()
                or "RESOURCE_EXHAUSTED" in err_msg.upper()
                or "QUOTA" in err_msg.upper()
                or "HIGH DEMAND" in err_msg.upper()
                or "TEMPORARY" in err_msg.upper()
            )
            if is_retryable and attempt < max_retries - 1:
                print(
                    f"Gemini API rate limit or server load hit (429/503). Retrying in {delay:.1f}s... (Attempt {attempt + 1}/{max_retries})"
                )
                time.sleep(delay)
                delay *= 2.0  # Exponential backoff
            else:
                raise e
