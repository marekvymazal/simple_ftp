import sys
import os
import getopt

from .ftp import FTP

def main():
    """The main routine."""
    argv = sys.argv[1:]

    help_str = """
    -h,--help                  Show help
    --view [directory]         List files in directory
    --crawl                    Crawl up subdirectories
    --username [username]      Set username
    --password [password]      Set password
    --connection [connection]  What to connect to

    q, quit, exit == exits console
    connect [connection] [username] [password]
    disconnect
    view [path]
    crawl [path]

    TODO: create command line function to upload file to ftp quickly
    """

    try:
        opts, args = getopt.getopt(argv,"hi",["help"])

    except getopt.GetoptError:
        print(help_str)
        sys.exit(2)

    for opt, arg in opts:

        if opt in ('-h', '--help'):
            print (help_str)
            sys.exit()
            return


    connected = False
    ftp = None

    while True:
        s = input('command:')

        try:
            if s.split()[0] == 'connect':
                connection = s.split()[1]
                username = s.split()[2]
                password = s.split()[3]

                ftp = FTP()
                #ftp = FTP(debug=False)
                #ftp.target_folder = website_root
                #ftp.export_folder = website_export_path

                # TODO: more excludes to settings.xml
                #ftp.set_exclude_files(exclude_files) # files to not upload no matter what
                #ftp.set_exclude_folders(exclude_folders)
                #ftp.set_exclude_folders(exclude_roots, root=True) # root folders to leave alone

                ftp.connect(connection, username, password)
        except:
            pass

        try:
            if s.split()[0] == 'view':
                path = s.split()[1]
                ftp.view( path )
        except:
            pass

        try:
            if s.split()[0] == 'crawl':
                path = s.split()[1]
                ftp.view( path, crawl=True )
        except:
            pass

        try:
            if s.split()[0] == 'disconnect':
                ftp.disconnect()
        except:
            pass

        if s in ['q','quit','exit']:
            print("Quit simple_ftp\n")
            if ftp != None:
                ftp.disconnect()
            return

if __name__ == "__main__":
    main()
