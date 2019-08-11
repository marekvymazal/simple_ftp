import ftplib
import os

colors = {
    'HEADER' :'\033[95m',
    'BLUE' : '\033[94m',
    'GREEN' : '\033[92m',
    'YELLOW' : '\033[93m',
    'RED' : '\033[91m',
    'END' : '\033[0m',
    'BOLD' : '\033[1m',
    'UNDERLINE' : '\033[4m'
}

class FTP:

    def __init__(self, debug=False):
        self.ftp = None

        self.export_folder = ''#'/home/user/Exports/Website'
        #if (os.name == "posix"):
        #    self.export_folder = '/Users/user/Exports/Website'

        self.target_folder = ''#'/public_html'
        self.debug = debug

        self.exclude_files = [] # files to not upload no matter what
        self.exclude_root_folders = [] # root folders to leave alone

        self.delete_if_found = [] # files to delete if found

        self.use_extensions = False
        self.include_extensions = [] # file extensions to include when uploading

        self.process_files = True # enable upload and deleting files
        self.process_folders = True # enable upload and deleting folders

        self.force_upload_files = False
        self.force_delete_files = False

        self.force_upload_folders = False
        self.force_delete_folders = False

        self.process_uploaded_files = 0
        self.process_uploaded_folders = 0
        self.process_deleted_files = 0
        self.process_deleted_folders = 0


    def connect(self, ftp_site, username, password):
        '''
        Connect to ftp
        '''
        self.ftp = ftplib.FTP(ftp_site)
        self.ftp.login(username, password)
        print('FTP connect: ' + ftp_site)


    def set_exclude_files( self, files ):
        """
        Set file names to be excluded from uploads
        """
        self.exclude_files = files


    def set_exclude_folders( self, folders, root=False ):
        """
        Sets folders to exclude from uploads

        root=True|False
        Root folders are only excluded if they are directly under the base folder
        """
        if root == True:
            self.exclude_root_folders = folders
        else:
            self.exclude_folders = folders


    def set_delete_if_found( self, files ):
        self.delete_if_found = files


    def reset_process_counts(self):
        self.process_uploaded_files = 0
        self.process_uploaded_folders = 0
        self.process_deleted_files = 0
        self.process_deleted_folders = 0


    def print_file( self, file, depth=0 ):
        padding = '  ' + ('  ' * depth)
        print(colors['BLUE'] + padding + file + colors['END'])


    def upload(self, server_file, local_file, make_directories=False, depth=0):
        """
        Uploads local file to target server_file destination
        if directories do not exist on ftp then they are automatically generated
        """
        if self.ftp == None:
            return False

        server_file = os.path.join( self.target_folder, server_file )

        #print("Server:" + server_file)
        #print("Local :" + local_file)

        # check if file exists
        if not os.path.isfile(local_file):
            raise ValueError('file does not exist: ' + local_file )

        padding = '+ ' + ('  ' * depth)
        #print(padding + server_file)
        print(colors['GREEN'] + padding + server_file + colors['END'])

        self.process_uploaded_files += 1

        #print ('FTP uploaded: ' + server_file)
        if not self.debug:
            #self.delete( server_file )
            try:
                self.ftp.storbinary("STOR " + server_file, open(local_file, "rb"))
            except Exception as e:
                #print(e)
                if str(e).split(' ')[0] =='550':
                    # check if directories exist and then try again
                    rel_dir = server_file[len(self.target_folder):]
                    #print('make dirs at: ' + rel_dir)
                    self.mkdirs( rel_dir )
                #raise ValueError(e)


    def delete(self, server_file, depth=0):

        if self.ftp == None:
            return False

        padding = '- ' + ('  ' * depth)
        #print(padding + self.target_folder + '/' + server_file)
        print(colors['RED'] + padding + self.target_folder + '/' + server_file + colors['END'])

        self.process_deleted_files += 1

        if not self.debug:
            result = self.ftp.delete(self.target_folder + '/' + server_file)
            #print(result)


    def delete_folder(self, folder_path, depth=0 ):

        if self.ftp == None:
            return False

        padding = '- ' + ('  ' * depth)
        #print(padding + self.target_folder + '/' + folder_path)
        print(colors['RED'] + padding + self.target_folder + '/' + folder_path + '/' + colors['END'])

        self.process_deleted_folders += 1

        dir, files = self.get_ftp_files( folder_path )

        for f in files:
            if not self.debug:
                self.delete( folder_path + '/' + f, depth=depth+1)

        for d in dir:
            self.delete_folder( folder_path + '/' + d, depth=depth+1)

        if not self.debug:
            self.ftp.rmd(self.target_folder + '/' + folder_path)


    def create_folder(self, folder_path, depth=0):

        if self.ftp == None:
            return False

        padding = '+ ' + ('  ' * depth)
        print(colors['GREEN'] + padding + self.target_folder + '/' + folder_path + '/' + colors['END'])

        self.process_uploaded_folders += 1

        if not self.debug:
            self.ftp.mkd( self.target_folder + '/' + folder_path )


    def set_permission(self, file, permission):
        if not self.debug:
            self.ftp.sendcmd('SITE CHMOD ' + permission + ' ' + file)


    def close(self):
        self.ftp.quit()
        print('FTP quit')


    def disconnect(self):
        self.close()


    def filter_files( self, file_list ):
        filtered = []

        for _file in file_list:
            filename, ext = os.path.splitext(_file)

            if self.use_extensions and ext != '':
                if ext not in self.include_extensions:
                    continue

            filtered.append(_file)

        return filtered


    def filter_files_global( self, file_list, reldir ):
        filtered = []
        for _file in file_list:
            if _file in self.exclude_files:
                continue

            test_path = os.path.join( reldir, _file )
            if test_path in self.exclude_root_folders:
                continue

            filtered.append(_file)

        return filtered


    def get_local_files( self, reldir):

        fulldir = os.path.join(self.export_folder, reldir)

        # get local files
        local_list = os.listdir( fulldir )

        # remove hidden files
        local_list = [f for f in local_list if not f.startswith('.')]
        #for f in local_list:
        #    if f.startswith('.'):
        #print(local_list)


        local_files = []
        local_dirs = []
        for file in local_list:
            fullfile = os.path.join(fulldir, file)

            # process file
            if os.path.isfile(fullfile):
                local_files.append(file)

            # process directory
            if os.path.isdir(fullfile):
                local_dirs.append(file)

        return local_dirs, local_files


    def get_ftp_files( self, reldir ):
        ftp_list = []

        #try:
        #    ftp_list = self.ftp.nlst(self.target_folder + '/' + reldir)
        #except Exception as ex:
        #    print(ex)

        #print(self.ftp.pwd())
        self.ftp.cwd('/') # reset current directory to ftp root

        try:
            self.ftp.cwd(self.target_folder + '/' + reldir) # change directory to reldir
        except Exception as ex:
            print(ex)

        self.ftp.retrlines("NLST -a", ftp_list.append)
        for item in ['.','..']:
            ftp_list.remove(item)

        self.ftp.cwd('/')

        for i in range(len(ftp_list)):
            ftp_list[i] = ftp_list[i].split('/')[-1]

        ftp_files = []
        ftp_dirs = []
        for file in ftp_list:
            if '.' in file:
                if file in self.delete_if_found:
                    self.delete( file )
                else:
                    ftp_files.append(file)
            else:
                ftp_dirs.append(file)

        return ftp_dirs, ftp_files


    def view( self, reldir, depth=0, crawl=False ):
        if depth == 0:
            print('\n')
            print(reldir)

        padding = '  '*(depth+1)
        dirs, files = self.get_ftp_files( reldir )

        for f in files:
            print(padding + f)

        for f in dirs:
            print(padding + f + '/')
            if crawl==True:
                self.view(reldir + '/' + f, depth=(depth+1), crawl=crawl)


    def mkdirs( self, file_path ):

        name, ext = os.path.splitext(file_path)
        is_dir = ext == ''

        path = file_path
        if not is_dir:
            path = os.path.dirname(path)

        path_folders = path.split('/')
        path_folders = [f for f in path_folders if f != '']

        rel_dir = ''
        for folder in path_folders:

            ftp_dirs, ftp_files = self.get_ftp_files( rel_dir )

            if not folder in ftp_dirs:
                new_folder = os.path.join( rel_dir, folder )
                self.create_folder( new_folder )

            rel_dir += '/' + folder


    def make_target(self):

        folders = self.target_folder.split('/')

        cur_folder = ''
        for folder in folders:
            cur_folder += folder + '/'
            try:
                self.ftp.cwd(cur_folder)
                self.ftp.cwd('/')
                self.print_file(self.target_folder)
            except Exception as e:
                print(e)
                print(colors['GREEN'] + '+ ' + cur_folder + colors['END'])
                self.ftp.mkd( cur_folder )

        self.ftp.cwd('/')


    def ProcessDirectory( self, reldir, crawl=False, depth=0 ):

        if depth == 0:
            print("\nprocessing directory")
            self.reset_process_counts()


            # check if local folder exists
            if not os.path.isdir(self.export_folder + '/' + reldir ):
                raise ValueError("Could not find local directory:" + self.export_dir + '/' + reldir)

            # check if ftp folder exists
            try:
                self.ftp.cwd(self.target_folder + '/' + reldir)
                self.ftp.cwd('/')
                self.print_file(self.target_folder + '/')
            except Exception as e:
                print(e)
                if str(e).split(' ')[0] =='550':
                    self.make_target()
                    self.mkdirs(reldir)

        else:
            self.print_file( reldir.split('/')[-1] + '/', depth=depth)


        pad_inc = "  "
        padding = pad_inc * depth
        fulldir = os.path.join(self.export_folder, reldir)

        # get local files
        local_dirs, local_files = self.get_local_files( reldir )
        local_files = self.filter_files_global(local_files, reldir)
        local_dirs = self.filter_files_global(local_dirs, reldir)

        # get server files
        ftp_dirs, ftp_files = self.get_ftp_files( reldir )
        ftp_files = self.filter_files_global(ftp_files, reldir)
        ftp_dirs = self.filter_files_global(ftp_dirs, reldir)

        # file process lists
        dir_to_add = list(set(local_dirs) - set(ftp_dirs))
        dir_to_del = list(set(ftp_dirs) - set(local_dirs))

        to_add = list(set(local_files) - set(ftp_files))
        to_del = list(set(ftp_files) - set(local_files))

        # filter files by extension
        to_add = self.filter_files( to_add )
        to_del = self.filter_files( to_del )

        if self.force_delete_files:
            ftp_files = self.filter_files( ftp_files )

        if self.force_upload_files:
            local_files = self.filter_files( local_files )

        # get unprocessed files and dirs
        skipped_files = list(set(ftp_files) - set(to_add) - set(to_del))
        skipped_dirs = list(set(ftp_dirs) - set(dir_to_add) - set(dir_to_del))

        # get all local files
        # get all ftp files

        # get files not in ftp // upload new // default
        # get files not in local // delete new // default

        # upload all files, filtered by extension // upload only files of extension

        # process files # default true
        # process dir # default true
        # crawl = process sub folders

        if self.process_files:

            for file in skipped_files:
                self.print_file( file, depth=depth+1)

            if self.force_delete_files:
                # delete all ftp files
                for file in ftp_files:
                    server_file = os.path.join(reldir, file)
                    self.delete( server_file, depth=depth+1 )
            else:
                # delete files not in local
                for file in to_del:
                    server_file = os.path.join(reldir, file)
                    self.delete( server_file, depth=depth+1 )


            if self.force_upload_files:
                # upload all local files
                #list(set().union(a,b,c))

                for file in local_files:
                    server_file = os.path.join(reldir, file)
                    fullfile = os.path.join(fulldir, file)
                    self.upload( server_file, fullfile, depth=depth+1 )
            else:
                for file in to_add:
                    server_file = os.path.join(reldir, file)
                    fullfile = os.path.join(fulldir, file)
                    self.upload( server_file, fullfile, depth=depth+1 )


        if self.process_folders:

            if crawl == False:
                for file in skipped_dirs:
                    self.print_file( file + '/', depth=depth+1)

            # delete folders
            if self.force_delete_folders:
                for file in ftp_dirs:
                    server_file = os.path.join(reldir, file)
                    self.delete_folder( server_file, depth=depth+1 )
            else:
                for file in dir_to_del:
                    server_file = os.path.join(reldir, file)
                    self.delete_folder( server_file, depth=depth+1 )

            # add folders
            if self.force_upload_folders:
                for file in local_dirs:
                    server_file = os.path.join(reldir, file)
                    self.create_folder( server_file, depth=depth+1 )
            else:
                for file in dir_to_add:
                    server_file = os.path.join(reldir, file)
                    self.create_folder( server_file, depth=depth+1 )

            if crawl == True:
                for file in local_dirs:
                    self.ProcessDirectory( os.path.join(reldir, file), crawl=crawl, depth=depth+1 )

        if depth==0:
            print('\n')
        # show uploaded / deleted count
        #if depth==0:
        #    print('\n')
        #    print('files uploaded   :' + str(self.process_uploaded_files))
        #    print('files deleted    :' + str(self.process_deleted_files))
        #    print('folders uploaded :' + str(self.process_uploaded_folders))
        #    print('folders deleted  :' + str(self.process_deleted_folders))
