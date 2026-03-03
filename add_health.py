with open("/root/freeeway/app.py", "r") as f:
    content = f.read()

# Verificar si ya existe health_check
if "health_check" not in content:
    with open("/root/freeeway/app.py", "r") as f:
        lines = f.readlines()
    
    health_code = '''
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()}), 200

'''
    insert_pos = 306
    lines.insert(insert_pos, health_code)
    
    with open("/root/freeeway/app.py", "w") as f:
        f.writelines(lines)
    print("Health endpoint added")
else:
    print("Health endpoint already exists")