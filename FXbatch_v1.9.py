from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image, ImageOps
from time import perf_counter
from os import scandir, path, sep, listdir, makedirs, stat
from random import choice
from tkinter import messagebox, filedialog
from pygubu.builder import Builder
from multiprocessing import cpu_count

PROJECT_PATH = path.abspath(path.dirname(__file__))
PROJECT_UI = path.join(PROJECT_PATH, "fx_v03.ui")

class FXbatch:
    
    def __init__(self, master=None):
        self.o_res = ''
        self.nu_res = ''
        self.res40 = ''

        # Load UI initialisation settings
        self.builder = builder = Builder()
        builder.add_resource_path(PROJECT_PATH)
        builder.add_from_file(PROJECT_UI)
        
        # Menu objects
        self.mainwindow = builder.get_object('frm_top', master)
        self.mainmenu = menu = builder.get_object('mainmenu', master)
        self.mainwindow['menu'] = menu
        
        # Load UI objects that are going disabled/enabled. Easier object calls
        self.o_slide = builder.get_object('scl_compress', master)
        self.o_comp = builder.get_object('tx_comp', master)
        self.o_h = builder.get_object('txt_h', master)
        self.o_w = builder.get_object('txt_w', master)
        self.o_lock = builder.get_object('chk_lk', master)
        self.o_per = builder.get_object('rd_percentage', master)
        self.o_pix = builder.get_object('rd_pixels', master)
        self.o_dpi = builder.get_object('txt_dpi', master)
        self.o_out = builder.get_object('txt_output', master)
        self.o_start = builder.get_object('btn_start', master)

        # Load UI all UI variables. Easier variable calls
        builder.import_variables(self, ['v_txt_in', 'chk_rz', 'rd_resize', 'v_width', 'v_hgt', 
        'chk_lock', 'v_org', 'v_new', 'v_dpi', 'v_size', 'rdb_img', 'v_comp', 'v_slide', 'v_cpu', 'v_txt_out',
        'v_prog', 'v_progbar', 'btn_text', 'v_num'])
        
        # Pygubu syntax to connect objects/variables to gui
        builder.connect_callbacks(self)

        # Set startup values
        # Lock ratio ON
        self.chk_lock.set(True)
        self.call_lock()
        # Set resize method Percentage
        self.rd_resize.set('per')
        # Set format to JPG
        self.rdb_img.set('1')
        # CPU cores set to the maximum
        cpucores = cpu_count()
        self.v_cpu.set(str(cpucores))
        # Set compression to 60 
        self.bind_slide()
        # Resize checkbox OFF
        self.reschk_action('disabled')

    # To have the same selected random image for comparison and reference
    global img_random

    # UI validation functions

    # *** Compression Section ***
    # Set number to slider    
    def bind_comp(self, event=None):
        vstring = self.v_comp.get()
        if vstring.isnumeric() and int(vstring) in range(20, 101):
            self.v_slide.set(vstring)
        else:
            self.v_slide.set(60)
            self.v_comp.set(60)

    # Set number to JPG compression on slide
    def call_slide(self, event=None):
        self.v_comp.set(self.v_slide.get())

    # Doubleclick slider to reset JPG compression to 60
    def bind_slide(self, event=None):
        self.v_slide.set(60)
        self.v_comp.set(self.v_slide.get())

    # JPG radio button trigger to disable compression
    def call_format(self, event=None):
        val = self.rdb_img.get()
        if val > 1:
            self.jpg_action('disabled')
        else: # val == 1:
            self.jpg_action('normal')
        # elif val == 0:
        #     self.jpg_action('normal')
        #     # self.v_slide.set(80)
        #     # self.call_slide()


    def jpg_action(self, status):
        self.o_comp.configure(state=status)
        self.o_slide.configure(state=status)

    
    # *** Resize Section ***
    # Resolution checkbox functionality
    def call_lock(self, event=None):
        if self.chk_lock.get():
            self.o_h.configure(state='disabled')
        else:
            self.o_h.configure(state='enabled')

    # Functionality resize percentage radio button
    def call_perpix(self, event=None):
        file_check = self.v_txt_in.get()
        rd_id = self.rd_resize.get()
        if path.exists(file_check):
            if len(file_check) > 3:
                if rd_id == 'per':
                    self.resetwh()
                if rd_id == 'pix':
                    self.setwh(file_check)

# Utility: Reset width and hieght
    def resetwh(self, event=None):
        self.v_width.set(40)
        self.v_hgt.set(40)
        self.chk_lock.set(True)
        self.v_new.set(self.res40)
        self.o_h.configure(state='disabled')
        self.rd_resize.set('per')

# Utility: Set width and hieght 
    def setwh(self, folder):
        ow = int(self.o_res.split('x')[0])
        oh = int(self.o_res.split('x')[-1])
        self.v_width.set(ow)
        self.v_hgt.set(oh)
        self.chk_lock.set(True)
        self.v_new.set(str(ow) + ' x ' + str(oh))
        self.o_h.configure(state='disabled')

    def call_resize(self, event=None):
        self.chk_lock.set(True)
        self.call_lock()
        self.rd_resize.set('per')
        if self.chk_rz.get():
            self.reschk_action('normal')
        else:
            self.reschk_action('disabled')

    def reschk_action(self, status):
        self.o_pix.configure(state=status)
        self.o_per.configure(state=status)
        self.o_w.configure(state=status)
        self.o_lock.configure(state=status)
        self.o_dpi.configure(state=status)

    # For Menu item <Quit>
    # def on_quit(self, event=None):
    #     self.mainwindow.quit()
    

    #  *** Input Section ***
    # Set input folder and default output folder on button click
    def call_input(self, events=None):
        
        in_folder = filedialog.askdirectory()
        if path.exists(in_folder):
            self.imgstats(in_folder)
    
    # Load image info into gui.
    def imgstats(self, folder):
        global valid_in, valid_out
        try:
            f_random = choice([x for x in listdir(folder) if path.isfile(path.join(folder, x))])
            random_img = Image.open(folder + sep + f_random)      
        except:
            messagebox.showwarning('No valid Images', 'Sorry, there are no valid images in this folder')
            valid_in = False
            valid_out = False
        else:
            self.load_imgstats(folder, random_img)
            self.load_filestats(folder)
            valid_in = True
            valid_out = True
            
    # Load folder size and number of files
    def load_filestats(self, folder):
        size = 0
        files = 0
        for ele in scandir(folder):
            size += stat(ele).st_size
            if ele.is_file():
                files += 1
        self.v_size.set(str(round(size / (1024 * 1024))) + ' Mb')
        self.v_num.set(str(files))


    # Load random image info
    def load_imgstats(self, folder, img):
        self.inputset(folder)
        h = img.height
        w = img.width
        org = str(w) + " x " + str(h)
        dp = str(img.info['dpi'])
        dpstrip = dp.split(',')[0]
        dpnew = dpstrip.lstrip('(')
        dpnew = int(float(dpnew))
        self.v_dpi.set(dpnew)
        self.v_org.set(org)
        wper = int(self.v_width.get())
        hper = int(self.v_hgt.get())

        nuw = int(wper*w/100)
        nuh = int(hper*h/100)
        nu = str(nuw) + " x " + str(nuh)
        self.v_new.set(nu)
        
        self.nu_res = self.v_new.get()
        self.res40 = self.nu_res
        self.o_res = self.v_org.get()

    # Load input variables on button click
    def inputset(self, folder):
        if len(folder) > 3: # Checking if its not filling in blank lines
            in_folder = folder + '/'
            out_folder = folder + '/Resized/'
        else:
            in_folder = folder
            out_folder = folder + 'Resized/'
        self.v_txt_in.set(in_folder)
        self.v_txt_out.set(out_folder)
        self.o_out.configure(state='enabled')
        self.rd_resize.set('per')
        self.chk_rz.set(True)
        self.reschk_action('enabled')

    # Callback from GUI - width update.
    def bind_w(self, event=None):
        ow = int(self.o_res.split('x')[0])
        oh = int(self.o_res.split('x')[-1])
        per_range = range(9, 101)
        if valid_in:
            if self.rd_resize.get() == 'per':
                if self.chk_lock.get() and self.v_width.get().isnumeric():
                    w = int(self.v_width.get())
                    if w in per_range:
                        self.v_hgt.set(w)
                        nuw = int(ow*w/100)
                        nuh = int(oh*w/100)
                        self.nu_res = str(nuw) + " x " + str(nuh)
                        self.v_new.set(self.nu_res)
                    else:
                        self.resetwh()
                else:
                    if self.v_width.get().isnumeric() and self.v_hgt.get().isnumeric():
                        w = int(self.v_width.get())
                        h = int(self.v_hgt.get())
                        if w in per_range and h in per_range:
                            nuw = int(ow*w/100) 
                            nuh = int(oh*h/100)
                            self.nu_res = str(nuw) + " x " + str(nuh)
                            self.v_new.set(self.nu_res)
                        else:
                            self.resetwh()
                    else:
                        self.resetwh()
            else:
                if self.chk_lock.get():
                    if self.v_width.get().isnumeric():
                        w = int(self.v_width.get())
                        ow = int(self.o_res.split('x')[0])
                        oh = int(self.o_res.split('x')[-1])
                        if ow > oh:
                            res_ratio = oh/ow
                        else:
                            res_ratio = ow/oh
                        nuh = int(w * res_ratio)
                        self.nu_res = str(w) + " x " + str(nuh)
                        self.v_new.set(self.nu_res)
                        self.v_hgt.set(nuh)
                    else:
                        self.resetwh()
                else:
                    w = self.v_width.get()
                    h = self.v_hgt.get()
                    if w.isnumeric() and h.isnumeric():
                        self.nu_res = str(w) + " x " + str(h)
                        self.v_new.set(self.nu_res)
                    else:
                        self.resetwh()


# Code check from below:
# To do:
# Done: 1. Fix image stats issues
# 2. Sort all image conversion options
# 3. Write Help file and sort menu
# 4. Write About file and sort out content
# 5. Create windows exe and test


    # Callback from GUI - hieght update. 
    def h_update(self, event=None):
        if len(self.v_txt_in.get()) > 3:
            rd_flag = self.rd_resize.get()
            h_var = self.v_org.get()
            id_flag = 'h'
            self.wh_update(rd_flag, h_var, id_flag)
        else:
            self.resetwh
    
    #  Common function which checks if radio button is percentage or pixels
    def wh_update(self, rd_flag, var, id_f):
        if str(var).isdigit():
            rng = (5, 100)
            r_lock = self.chk_lock.get()
            self.o_res = self.v_org.get()
            ow = int(self.o_res.split('x')[0])
            oh = int(self.o_res.split('x')[-1])
            if rd_flag == 'per':
                if var in rng:
                    nw = ow * var/100
                    if r_lock:
                        nh = oh * var/100
                    else:
                        nh = oh
                    nures = str(nw) + 'x' + str(nh)
                    self.v_new.set(nures)
                else:
                    self.resetwh()
                    
            if rd_flag == 'pix':
                if r_lock and id_f == 'w':
                    nw = var
                    nh = oh * ow/oh
                elif not r_lock and id_f == 'w':
                    nw = var
                    nh = oh
                elif id_f == 'h':
                    nw = ow
                    nh = var
                nures = str(nw) + 'x' + str(nh)
                self.v_new.set(nures)
            else:
                self.resetwh()
        else:
            self.resetwh()
    
    # Load output variables on button click
    def call_output(self, events=None):
        incheck = self.v_txt_in.get()
        if len(incheck) > 0:
            out_folder = filedialog.askdirectory()
            if path.exists(out_folder):
                self.v_txt_out.set(out_folder)
            else:
                if out_folder.split('/')[-1] == "Resized":
                    out_folder = out_folder.split('/')[0]
                if not path.exists(out_folder):
                    out_folder = "" 
                self.v_txt_out.set(out_folder)
        else:
            messagebox.showwarning("File Input Error", 'Please select input folder first')

    # Callback function from gui - input field
    def bind_input(self, events=None):
        in_check = self.v_txt_in.get()
        if not path.exists(in_check):
            self.v_txt_in.set("")
    
    # Callback function from gui - output field
    def bind_output(self, events=None):
        out_check = self.v_txt_out.get()
        if not path.exists(out_check):
            out_fix = out_check.rstrip('Resized/')
            if not path.exists(out_fix):
                self.v_txt_out.set("")
  
# Start image processing

        # Start batch resize
    def call_start(self):
        #  Opt to pass variables instead of global. Other: ext, 
        global inpath, outpath, img_w, img_h, img_dpi, img_compress, imgext #, exts, fixfileimages, fcount, core, prog_step

        self.btn_text.set('Processing: Please wait')
        self.o_start.configure(state='disabled')

        self.mainwindow.update()

        inpath = self.v_txt_in.get()
        outpath = self.v_txt_out.get()
        img_w = int(self.v_width.get())
        img_h = int(self.v_hgt.get())
        img_dpi = int(self.v_dpi.get())
        img_compress = int(self.v_comp.get())
        res_opt = self.rd_resize.get()

        imgext = self.getext(self.rdb_img.get())

        exts = ['jpeg', 'jpg', 'png', 'gif', 'ico', 'tif', 'tiff','tga', 'bmp', 'webp', 'wmf']
        
        rawfileimgs = listdir(inpath)
        fixfileimages = self.fixlist(rawfileimgs, exts)
        fcount = len(fixfileimages)

        start = perf_counter()

        if not path.exists(outpath):
            makedirs(outpath)
        
        # run_process()
        core = int(self.v_cpu.get())
        prog_step = 100 / fcount
        count = 0

        with ThreadPoolExecutor(max_workers = core) as t:

            # Main image processing loop with multi-threading
            futures = [t.submit(self.resize_img, imgs, res_opt) for imgs in fixfileimages]
            
            # Keep alive loop to update gui with file conversion info
            for fut in as_completed(futures):
                count += 1
                newprog = count * prog_step
                shwlbl = 'Processing: {}/{} files'.format(count, fcount)
                self.v_prog.set(shwlbl)
                self.v_progbar.set(newprog)
                self.mainwindow.update()

        # Reset gui and check conversion counter
        self.v_prog.set('')
        end = perf_counter()
        prtime = end - start

        # Load new folder size
        nusize = self.load_resfilestats(outpath)

        # Show file conversion message
        shwmsg3 = '{} Files processed in {} seconds'.format(fcount, "{:.2f}".format(prtime))
        shwmsg2 = 'Previous size: {}'.format(self.v_size.get())
        shwmsg1 = 'Current size: {}'.format(nusize)
        lines = [shwmsg3, shwmsg1 + "  (" + shwmsg2 + ")"]

        # Message with conversion stats
        messagebox.showinfo("File Resize Complete", "\n".join(lines))

        # Reset gui for next run
        self.o_start.configure(state='enabled')
        self.btn_text.set('Process Images')
        self.v_progbar.set(0)

    # Main image resize function. This will convert the image and save the file
    def resize_img(self, imgfile, res_opt):
        infix = f"{inpath}/"
        outfix = f"{outpath}/"
        
        f_img = imgfile.split('.')[0]

        img = Image.open(infix + imgfile)

        ex = img.getexif()

        # Check if pixel or percentage has been selected
        if res_opt == 'per':
            nuh = int(img.height*img_h/100)
            nuw = int(img.width*img_w/100)
            img_final = img.resize((nuw,nuh))
        else:
            nuh = img_h
            nuw = img_w
            img_final = img.resize((nuw,nuh))

        img_final = ImageOps.exif_transpose(img_final)
        img_final = img_final.convert('RGB')

        # 1=JPG, 2=PNG, 3=WEBP, 4=ICO, 5=TIF, 6=TGA
        fpath = f"{outfix}{f_img}.{imgext}"
        
        if imgext == 'jpg':
            img_final.save(fpath, 'JPEG', quality=img_compress, dpi=(img_dpi, img_dpi))
        elif imgext == 'png':
            img_final.save(fpath, 'PNG', dpi=(img_dpi, img_dpi))
        elif imgext == 'webp':
            img_final.save(fpath, 'WEBP', quality=img_compress, dpi=(img_dpi, img_dpi))
        elif imgext == 'ico':
            img_final.save(fpath, 'ICO')
        elif imgext == 'tif':
            img_final.save(fpath)
        elif imgext == 'tga':
            img_final.save(fpath, 'TGA')

        img = None
        img_final = None
    
    # Load resize folder size
    def load_resfilestats(self, folder):
        size = 0
        for ele in scandir(folder):
            size += stat(ele).st_size

        re_size = str(round(size / (1024 * 1024))) + ' Mb'
        return re_size

    # Check and load all image files and ignore all other folders etc
    def fixlist(self, rawfileimgs, exts):
        newlist = []
        for file in rawfileimgs:
            ext = file.split('.')[-1]
            if ext.lower() in exts:
                newlist.append(file)
        return newlist

    def getext(self, ext):
        # 1=JPG, 2=PNG, 3=WEBP, 4=ICO, 5=TIF, 6=TGA
        if ext == 1:
            return 'jpg'
        if ext == 2:
            return 'png'
        if ext == 0:
            return 'webp'
        if ext == 4:
            return 'ico'
        if ext == 5:
            return 'tif'
        if ext == 6:
            return 'tga'

    # Mainloop for gui
    def run(self):
        self.mainwindow.mainloop()


if __name__ == '__main__':
    app = FXbatch()
    app.run()
