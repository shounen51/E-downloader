import socket
import time

class ip_checker():
    def __init__(self):
        self.ip = self.__get_local_ip()
        print(f"Your ip is {self.ip}")
    
    def __get_local_ip(self):
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        return ip

    def wait_ip_change(self, sec=-1):
        ts = time.time()
        while time.time() - ts < sec or sec == -1:
            now_ip = self.__get_local_ip()
            if now_ip != self.ip:
                self.ip = now_ip
                print(f"Detect ip change. Your ip is {self.ip}")
                return True
            sleep_time = min(20, sec-(time.time()-ts))
            time.sleep(sleep_time)
        return False
    
if __name__ == "__main__":
    ipc = ip_checker()
    ipc.wait_ip_change(60)