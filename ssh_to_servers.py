from datetime import datetime

import paramiko
import pandas as pd

df = pd.read_excel('servers.xlsx')
username = "root"

grid_df = df[df['type'] == 'Grid']
text_xml_template = '<qa:browsers xmlns:qa="urn:config.gridrouter.qatools.ru">'
dealer_crawler_filename = 'start_dealer_crawler_cron.sh'
for index, ip in grid_df['IP'].items():
    text_xml_template += f"""
                    <browser name="chrome" defaultVersion="latest">
                        <version number="latest">
                            <region name="{index+1}">
                                <host name="{ip}" port="4444" count="12"/>
                            </region>
                        </version>
                    </browser>
                    
                    """
text_xml_template += "</qa:browsers>"
with open('grid.sh', 'r') as file:
    github_script = file.read()

with open('loadbalancer.sh', 'r') as file:
    loadbalancer_script = file.read()

with open('crawler.sh', 'r') as file:
    crawler_script = file.read()

with open('clean_up.sh', 'r') as file:
    clean_up_script = file.read()

check_status = []
errors = []

for index, row in df.iterrows():
    print('started : ', datetime.now())
    password = row['password']
    server = row['IP']
    type = row['type']
    try:
        client = paramiko.client.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(server, username=username, password=password)
        stdin, stdout, stderr = client.exec_command("/bin/bash", timeout=60)
        stdin.write(clean_up_script + '\n')
        stdin.flush()
        print(f'waiting for the cleanup to finish on server {server}')
        for line in stdout:
            print(line.strip())
        stdin.close()
        stdout.close()
        stderr.close()
        if type == 'Grid':
            check_status.append(f'{server}:4445/status')
            print(f'running script on server {server} for Grid')
            stdin, stdout, stderr = client.exec_command("/bin/bash", timeout=800)
            stdin.write(github_script+'\n')  # Append a newline character to simulate pressing Enter
            stdin.flush()  # Flush the buffer to ensure the script is sent to the server
            # exit_status = stdout.channel.recv_exit_status()  # Wait for the script to finish executing
            print('waiting for the script to finish')
            # Print the output of the script
            for line in stdout:
                print(line.strip())
            stdin.close()
            stdout.close()
            stderr.close()
            stdin, stdout, stderr = client.exec_command("bash create_selenoid_env.sh", timeout=1000)
            for line in stdout:
                print(line.strip())
            stdin, stdout, stderr = client.exec_command("bash start_selenoid_cron.sh", timeout=1000)
            for line in stdout:
                print(line.strip())
        elif type == 'Load Balancer':
            check_status.append(f'{server}:4444/ping')
            print(f'running script on server {server} for Load Balancer')
            filename = '/etc/grid-router/quota/test.xml'

            stdin, stdout, stderr = client.exec_command('cat > {} <<EOF\n{}\nEOF'.format(filename, text_xml_template))
            for line in stdout:
                print(line.strip())
            stdin.close()
            stdout.close()
            stderr.close()
            stdin, stdout, stderr = client.exec_command("/bin/bash", timeout=800)
            stdin.write(loadbalancer_script + '\n')  # Append a newline character to simulate pressing Enter
            stdin.flush()  # Flush the buffer to ensure the script is sent to the server
            # exit_status = stdout.channel.recv_exit_status()  # Wait for the script to finish executing
            print('waiting for the script to finish')
            # Print the output of the script
            for line in stdout:
                print(line.strip())
        elif type == 'Crawler':
            check_status.append(f'{server}:4445/status')
            print(f'running script on server {server} for Crawler')
            stdin, stdout, stderr = client.exec_command("/bin/bash", timeout=800)
            stdin.write(crawler_script + '\n')  # Append a newline character to simulate pressing Enter
            stdin.flush()  # Flush the buffer to ensure the script is sent to the server
            # exit_status = stdout.channel.recv_exit_status()  # Wait for the script to finish executing
            print('waiting for the script to finish')
            # Print the output of the script
            # Loop over both stdout and stderr
            while True:
                # Check if there is data available on either stream
                if stdout.channel.recv_ready():
                    stdout_line = stdout.readline().strip()
                    if stdout_line:
                        print('STDOUT:', stdout_line)
                if stderr.channel.recv_ready():
                    stderr_line = stderr.readline().strip()
                    if stderr_line:
                        print('STDERR:', stderr_line)

                # Exit loop if both streams are closed
                if stdout.channel.closed and stderr.channel.closed:
                    break

            stdin.close()
            stdout.close()
            stderr.close()
            stdin, stdout, stderr = client.exec_command("cat start_dealer_crawler_cron.sh", timeout=100)
            dealer_crawler = ''
            for line in stdout:
                print(line.strip())

                dealer_crawler += line.strip() + '\n'
            for error in stderr:
                print(error.strip())

            dealer_crawler = dealer_crawler.replace('104.238.228.193', df[df['type'] == 'Load Balancer']['IP'].iloc[0])
            stdin, stdout, stderr = client.exec_command('cat > {} <<EOF\n{}\nEOF'.format(dealer_crawler_filename, dealer_crawler))
            for line in stdout:
                print(line.strip())
            for error in stderr:
                print(error.strip())

            stdin.close()
            stdout.close()
            stderr.close()
            stdin, stdout, stderr = client.exec_command("bash create_python_env.sh\n", timeout=800)
            for line in stdout:
                print(line.strip())
            for error in stderr:
                print(error.strip())
            stdin, stdout, stderr = client.exec_command("bash start_dealer_crawler_cron.sh\n", timeout=800)
            for line in stdout:
                print(line.strip())
            for error in stderr:
                print(error.strip())

        # Close the SSH connection
        client.close()
    except Exception as e:
        print(f'There was an error while running script on server {server}',e)
        errors.append(server)


print('Urls to test : ')
print(check_status)
if errors:
    print('There were errors while running script on following servers ', errors)

with open(f'./errors.log', 'w') as log_file:
    errors_list = ''
    log_file.write(str(errors))

