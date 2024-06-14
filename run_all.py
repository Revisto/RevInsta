import os
import subprocess

python_files = ["instagram_service/instagram_listener.py", "instagram_service/instagram_sender.py", "telegram_service/telegram_sender.py", "telegram_service/telegram_listener.py"]

def run_all_main_files():
    processes = []
    try:
        for python_file in python_files:
            env = os.environ.copy()
            env["PYTHONPATH"] = os.getcwd() + ":" + env.get("PYTHONPATH", "")
            process = subprocess.Popen(["python", python_file], env=env)
            processes.append(process)
        while True:  # Keep the script running
            pass
    except KeyboardInterrupt:
        print("\nCtrl+C received, terminating all processes")
        for process in processes:
            process.terminate()
        for process in processes:
            process.wait()

if __name__ == "__main__":
    run_all_main_files()