import ftplib
import os


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

        self.use_extensions = False
        self.include_extensions = [] # file extensions to include when uploading

        self.process_files = True # enable upload and deleting files
        self.process_folders = True # enable upload and deleting folders

        self.force_upload_files = False
        self.force_delete_files = False

        self.force_upload_folders = False
        self.force_delete_folders = False


    def connect(self, ftp_site, username, password):
        '''
        Connect to ftp
        '''
        self.ftp = ftplib.FTP(ftp_site)
        self.ftp.login(username, password)
        print('FTP connect')


    def cwd(self, path):
        '''
        Change working directory
        '''
        if self.ftp == None:
            return False

        #self.ftp.cwd("/public_html/" + path)
        print('FTP cwd ' + path)


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


    def upload(self, server_file, local_file, make_directories=False):
        """
        Uploads local file to target server_file destination
        if directories do not exist on ftp then they are automatically generated
        """
        if self.ftp == None:
            return False

        print("Server:" + server_file)
        print("Local :" + local_file)

        # check if file exists
        if not os.path.isfile(local_file):
            raise ValueError('file does not exist: ' + local_file )

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


    def delete(self, server_file):

        if self.ftp == None:
            return False

        #print('FTP deleted: ' + server_file)
        if not self.debug:
            result = self.ftp.delete(server_file)
            #print(result)


    def delete_folder(self, folder_path):

        if self.ftp == None:
            return False

        print ("delete folder path:" + folder_path)

        ftp_list = self.ftp.nlst(folder_path)
        for d in ftp_list:
            file_name = d.split('/')[-1]
            if '.' in file_name:
                print("delete file:" + file_name)
                if not self.debug:
                    self.delete(d)

        ftp_list = self.ftp.nlst(folder_path)
        for d in ftp_list:
            if d == folder_path:
                continue

            file_name = d.split('/')[-1]
            if not '.' in file_name:
                print("delete folder:" + file_name)
                self.delete_folder(d)

        if not self.debug:
            self.ftp.rmd(folder_path)


    def create_folder(self, folder_path):

        if self.ftp == None:
            return False

        if not self.debug:
            self.ftp.mkd( folder_path )


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
        ftp_list = self.ftp.nlst(self.target_folder + '/' + reldir)
        for i in range(len(ftp_list)):
            ftp_list[i] = ftp_list[i].split('/')[-1]

        ftp_files = []
        ftp_dirs = []
        for file in ftp_list:
            server_file = os.path.join(self.target_folder + '/' + reldir, file)
            if '.' in file:
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
        #path_folders.insert(0, '')
        #print(self.target_folder)
        #print(path_folders)

        rel_dir = ''
        for folder in path_folders:
            #print(folder)
            #print(rel_dir)

            ftp_dirs, ftp_files = self.get_ftp_files( rel_dir )
            #print(ftp_dirs)

            if not folder in ftp_dirs:
                new_folder = os.path.join( self.target_folder + rel_dir, folder )
                print("create folder=" + new_folder)
                self.create_folder( new_folder )

            rel_dir += '/' + folder



    def ProcessDirectory( self, reldir, crawl=False, depth=0 ):
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

        """
        #print ('ADD:')
        dir_to_add = list(set(local_filtered_dirs) - set(ftp_filtered_dirs))
        #print (dir_to_add)

        #print ('DEL:')
        dir_to_del = list(set(ftp_filtered_dirs) - set(local_filtered_dirs))
        #if depth == 0:
        #    dir_to_del = list(set(dir_to_del) - set(self.exclude_root_folders))
        #print (dir_to_del)

        #print ('ADD:')
        to_add = list(set(local_filtered_files) - set(ftp_filtered_files))
        #print (to_add)

        #print ('DEL:')
        to_del = list(set(ftp_filtered_files) - set(local_filtered_files))
        #print (to_del)
        """

        # get all local files
        # get all ftp files

        # get files not in ftp // upload new // default
        # get files not in local // delete new // default

        # upload all files, filtered by extension // upload only files of extension

        # process files # default true
        # process dir # default true
        # crawl = process sub folders


        if self.process_files:

            if self.force_delete_files:
                # delete all ftp files
                for file in ftp_files:
                    server_file = os.path.join(self.target_folder + '/' + reldir, file)
                    #print("delete file:" + server_file)
                    print(padding + pad_inc + "deleted > " + file )
                    self.delete( server_file )
            else:
                # delete files not in local
                for file in to_del:
                    server_file = os.path.join(self.target_folder + '/' + reldir, file)
                    #print("delete file:" + server_file)
                    print(padding + pad_inc + "deleted > " + file )
                    self.delete( server_file )


            if self.force_upload_files:
                # upload all local files
                #list(set().union(a,b,c))

                for file in local_files:
                    server_file = os.path.join(self.target_folder + '/' + reldir, file)
                    fullfile = os.path.join(fulldir, file)
                    #print("upload file:" + server_file)
                    print(padding + pad_inc + "uploaded > " + file )
                    self.upload( server_file, fullfile )
            else:
                for file in to_add:
                    server_file = os.path.join(self.target_folder + '/' + reldir, file)
                    fullfile = os.path.join(fulldir, file)
                    #print("upload file:" + server_file)
                    print(padding + pad_inc + "uploaded > " + file )
                    self.upload( server_file, fullfile )


        if self.process_folders:
            # delete folders
            if self.force_delete_folders:
                for file in ftp_dirs:
                    #print ('file:'+ file)
                    server_file = os.path.join(self.target_folder + '/' + reldir, file)
                    #print("delete dir:" + server_file)
                    print(padding + "deleted > /" + file )
                    self.delete_folder( server_file )
            else:
                for file in dir_to_del:
                    #print ('file:'+ file)
                    server_file = os.path.join(self.target_folder + '/' + reldir, file)
                    #print("delete dir:" + server_file)
                    print(padding + "deleted > /" + file )
                    self.delete_folder( server_file )

            # add folders
            if self.force_upload_folders:
                for file in local_dirs:
                    server_file = os.path.join(self.target_folder + '/' + reldir, file)
                    print(padding + "uploaded > /" + file )
                    #print("upload dir:" + server_file)
                    self.create_folder( server_file )
            else:
                for file in dir_to_add:
                    server_file = os.path.join(self.target_folder + '/' + reldir, file)
                    print(padding + "uploaded > /" + file )
                    #print("upload dir:" + server_file)
                    self.create_folder( server_file )

        for file in local_dirs:

            # check if included
            if crawl == False:
                continue

            print(padding + "/" + file)
            self.ProcessDirectory( os.path.join(reldir, file), crawl=crawl, depth=depth+1 )
