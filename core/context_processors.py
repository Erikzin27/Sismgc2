def user_theme(request):
    theme = "dark"
    try:
        if request.user.is_authenticated and hasattr(request.user, "profile"):
            theme = request.user.profile.tema or "dark"
    except Exception:
        theme = "dark"
    return {"user_theme": theme}
