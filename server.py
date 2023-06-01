import socket
import signal
import sys
import random
import datetime
import time

# Read a command line argument for the port where the server
# must run.
port = 8080
if len(sys.argv) > 1:
    port = int(sys.argv[1])
else:
    print("Using default port 8080")

# Start a listening server socket on the port
sock = socket.socket()
sock.bind(('', port))
sock.listen(2)
host = socket.gethostname()
server_IP = socket.gethostbyname(host)
print("[S]: server listening on host:", host," and IP:", server_IP, " with port:",port)

### Contents of pages we will serve.
# Login form
login_form = """
   <form action = "http://%s:%d" method = "post">
   Name: <input type = "text" name = "username">  <br/>
   Password: <input type = "text" name = "password" /> <br/>
   <input type = "submit" value = "Submit" />
   </form>
""" % (server_IP, port)
# Default: Login page.
login_page = "<h1>Please login</h1>" + login_form
# Error page for bad credentials
bad_creds_page = "<h1>Bad user/pass! Try again</h1>" + login_form
# Successful logout
logout_page = "<h1>Logged out successfully</h1>" + login_form
# A part of the page that will be displayed after successful
# login or the presentation of a valid cookie
success_page = """
   <h1>Welcome!</h1>
   <form action="http://%s:%d" method = "post">
   <input type = "hidden" name = "action" value = "logout" />
   <input type = "submit" value = "Click here to logout" />
   </form>
   <br/><br/>
   <h1>Your secret data is here:</h1>
""" %  (server_IP, port)

#### Helper functions
# Printing.
def print_value(tag, value):
    print "Here is the", tag
    print "\"\"\""
    print value
    print "\"\"\""
    print

# Signal handler for graceful exit
def sigint_handler(sig, frame):
    print('Finishing up by closing listening socket...')
    sock.close()
    sys.exit(0)
# Register the signal handler
signal.signal(signal.SIGINT, sigint_handler)


# TODO: put your application logic here!
# Read login credentials for all the users
user_pass = {}
file1 = open('passwords.txt', 'r')
lines1 = file1.readlines()
user_pass = {}
for line in lines1:
    line = line.replace("\n", "")
    split = line.split(" ", 1)
    user_pass.update({split[0]: split[1]})

# Read secret data of all the users
file2 = open('secrets.txt', 'r')
lines2 = file2.readlines()
secret_dict = {}
for line in lines2:
    line = line.replace("\n", "")
    split = line.split(" ", 1)
    secret_dict.update({split[0]: split[1]})

# data structure for cookies

cookie_dict = {}



### Loop to accept incoming HTTP connections and respond.
while True:
    print("http://%s:%d" % ( server_IP ,port))
    client, addr = sock.accept()
    req = client.recv(1024)

    # Let's pick the headers and entity body apart
    header_body = req.split('\r\n\r\n')
    headers = header_body[0]
    body = '' if len(header_body) == 1 else header_body[1]
    print_value('headers', headers)
    print_value('entity body', body)

    # TODO: Put your application logic here!
    # Parse headers and body and perform various actions
    html_content_to_send=None
    headers_to_send = ''
    
    cook_user = None
    token_val=None
    #cook_secr = None
    if "Cookie" in headers:
        split1 = headers.split("token=")
        split2 = split1[1].split("\r\n")
        token_val = split2[0]
        cook_user = cookie_dict.get(token_val)

    if len(body)==0:
        if "Cookie" in headers:
            if cook_user: # valid cookie
                secret = secret_dict.get(cook_user)
                html_content_to_send = success_page + secret
            else:
                html_content_to_send = bad_creds_page # if there's a cookie field but it doesn't match
        else:
            html_content_to_send=login_page
    else:
        if "logout" in body:
            html_content_to_send=logout_page
            time_format = "%a, %d %b %Y %H:%M:%S GMT"
            cur = datetime.datetime.now().strftime(time_format)
            headers_to_send = "Set-Cookie: token=; expires="+cur+"\r\n"
            if cook_user:
                cookie_dict.pop(token_val)
            
        else:
            split = body.split("&")
            user = split[0].split("=")[1]
            password = split[1].split("=")[1]
            if not(user and password):
                if "Cookie" in headers:
                    # if valid or invalid send according
                    if cook_user: # valid cookie
                        secret = secret_dict.get(cook_user)
                        html_content_to_send = success_page + secret
                    else:
                        html_content_to_send = bad_creds_page
                else:
                    # send bad cred
                    html_content_to_send = bad_creds_page 
            else:
                val = user_pass.get(user)
                if not val or val!=password:
                    if "Cookie" in headers:
                        #if valid, then send success else bad cred
                        if cook_user: # valid cookie
                            secret = secret_dict.get(cook_user)
                            html_content_to_send = success_page + secret
                        else:
                            html_content_to_send = bad_creds_page
                    else:
                        # send bad cred 
                        html_content_to_send = bad_creds_page
                else:
                    # passwords match 
                    if "Cookie" in headers:
                        # if valid, then send success else bad cred
                        if cook_user: # valid cookie
                            secret = secret_dict.get(cook_user)
                            html_content_to_send = success_page + secret
                        else:
                            html_content_to_send = bad_creds_page
                    else:
                        # new COOKIE, update
                        rand_val = random.getrandbits(64)
                        while rand_val in cookie_dict:
                            rand_val = random.getrandbits(64)
                        headers_to_send = "Set-Cookie: token=" + str(rand_val) + "\r\n"
                        cookie_dict.update({str(rand_val) : user})
                        secret = secret_dict.get(user)
                        html_content_to_send = success_page + secret


    # Construct and send the final response
    response  = 'HTTP/1.1 200 OK\r\n'
    response += headers_to_send
    response += 'Content-Type: text/html\r\n\r\n'
    response += html_content_to_send
    print_value('response', response) 
    print(cookie_dict)  
    client.send(response)
    client.close()
    
    print "Served one request/connection!"
    print

#make a cookie helper method 

# We will never actually get here.
# Close the listening socket
sock.close()
