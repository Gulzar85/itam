def can_approve_request(user, request_obj):
    # 1. IT Admin ke paas khuli ijazat hai
    if user.role == 'IT_ADMIN':
        return True

    # 2. Manager Check: Kya request karne wala banda is user ka subordinate hai?
    # Hum 'user.role' check karenge taake sirf Manager/Admin hi action le sakein
    if user.role in ['MANAGER', 'IT_ADMIN']:
        if request_obj.user.manager == user:
            return True

    # 3. Hierarchy Check (Optional but Professional):
    # Agar aap chahte hain ke Manager ka Manager bhi approve kar sake,
    # toh humein recursive check lagana parega.

    return False
