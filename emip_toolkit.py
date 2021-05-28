"""
The EMIP Toolkit can be used under the CC 4.0 license
(https://creativecommons.org/licenses/by/4.0/)

Author: Naser Al Madi (nsalmadi@colby.edu)
"""

import math
import statistics
from PIL import Image, ImageDraw
from matplotlib import pyplot as plt
from matplotlib.pyplot import imshow
import numpy as np
from numpy.lib.ufunclike import fix
import pandas


class Fixation():
    ''' Basic container for storing Fixation data '''

    def __init__(self, trial, participant, timestamp, duration, x_cord, y_cord, token):
        ''' initalizes the basic data for each fixation:

			trial : int
			trial ID that the fixation belongs to.

			participant : int
			participant id that the fixation belongs to.

			timestamp : int
			fixation time stamp.

			duration : int
			fixation duration in milliseconds.

			x_cord : int
			fixation x coordinate.

			y_cord : int
			fixation Y coordinate.

			token : String
			the source code token which the fixation is on.
        '''

        self.trial_ID = trial
        self.participant = participant
        self.timestamp = timestamp
        self.duration = duration
        self.x_cord = x_cord
        self.y_cord = y_cord
        self.token = token


    def get_fixation(self):
        ''' returns fixation attributes as a list '''

        return [self.trial_ID,
        		self.participant,
        		self.timestamp,
        		self.duration,
        		self.x_cord,
        		self.y_cord,
        		self.token]

class SMIRed250_Fixation(Fixation):
    def __init__(self, trial, participant, timestamp, duration, x_cord, y_cord, token):
        super().__init__(trial, participant, timestamp, duration, x_cord, y_cord, token)

class EyeLink1000_Fixation(Fixation):
    def __init__(self, trial, participant, timestamp, duration, x_cord, y_cord, token, pupil):
        super().__init__(trial, participant, timestamp, duration, x_cord, y_cord, token)
        self.pupil = pupil

    def get_fixation(self):
        ''' returns fixation attributes as a list '''

        return super().get_fixation() + [self.pupil]

class Saccade():
    def __init__(self, trial, participant, timestamp, duration, x_cord, y_cord, x1_cord, y1_cord, amplitude, peak_velocity):
        ''' initalizes the basic data for each fixation:

			trial : int
			trial ID that the fixation belongs to.

			participant : int
			participant id that the fixation belongs to.

			timestamp : int
			fixation time stamp.

			duration : int
			fixation duration in milliseconds.

			x_cord : int
			fixation x coordinate.

			y_cord : int
			fixation Y coordinate.

            x1_cord : int
			fixation x1 coordinate.

			y1_cord : int
			fixation Y1 coordinate.

			amplitude : int
            amplitude.

            peak_velocity : int
            peak velocity.
        '''

        self.trial_ID = trial
        self.participant = participant
        self.timestamp = timestamp
        self.duration = duration
        self.x_cord = x_cord
        self.y_cord = y_cord
        self.x1_cord = x1_cord
        self.y1_cord = y1_cord
        self.amplitude = amplitude
        self.peak_velocity = peak_velocity

    def get_saccade(self):
        ''' returns saccade attributes as a list '''

        return [self.trial_ID,
                self.participant,
                self.timestamp,
                self.duration,
                self.x_cord,
                self.y_cord,
                self.x1_cord,
                self.y1_cord,
                self.amplitude,
                self.peak_velocity]

class EyeLink1000_Saccade(Saccade):
    def __init__(self, trial, participant, timestamp, duration, x_cord, y_cord, x1_cord, y1_cord, amplitude, peak_velocity):
        super().__init__(trial, participant, timestamp, duration, x_cord, y_cord, x1_cord, y1_cord, amplitude, peak_velocity)

class Blink():
    def __init__(self, trial, participant, timestamp, duration):
        ''' initalizes the basic data for each blink:

			trial : int
			trial ID that the fixation belongs to.

			participant : int
			participant id that the fixation belongs to.

			timestamp : int
			fixation time stamp.

			duration : int
			fixation duration in milliseconds.
        '''
        self.trial_ID = trial
        self.participant = participant
        self.timestamp = timestamp
        self.duration = duration

    def get_blink(self):
        ''' returns blink attributes as a list '''

        return [self.trial_ID,
                self.participant,
                self.timestamp,
                self.duration]

class EyeLink1000_Blink(Blink):
    def __init__(self, trial, participant, timestamp, duration):
        super().__init__(trial, participant, timestamp, duration)

class Trial():
    ''' Each trial consists of many samples that need to be converted to fixations.

    this class implements a fixation filter, fixation correction with offset, and
    drawing trial data as an image.

    A trial is part of an experiment. Or each experiment consists of multiple trials.
    '''

    def __init__(self, trial, participant, image):
        ''' initialize attributes for storing trial data, filtered fixations, and
        stores image name.

        trial : int
        trial number

        participant : String
        participant ID

        # EMIP Only
        data : String
		samples (SMPs) that belong to the trial

        image : String
        name of image file associated with trial
        '''

        self.trial_ID = trial
        self.trial_participant = participant

        self.offset_history = []

        self.trial_image = image

        self.fixations = []

    def get_trial_image(self):
        ''' returns the image file name associated with the trial '''
        return self.trial_image

    def get_fixation_number(self):
        ''' returns the number of filtered fixations in the trial '''
        return len(self.fixations)

    def get_fixations(self):
        ''' returns the filtered fixations in the trial '''
        return self.fixations

    def get_subject_ID(self):
        ''' returns subject ID '''
        return self.trial_participant

    def get_offset(self):
        ''' returns total offset applied by adding all offsets
        in offset history.
        '''

        x_total = 0
        y_total = 0

        for x_offset, y_offset in self.offset_history:
            x_total += (x_offset)
            y_total += (y_offset)

        return (x_total, y_total)

    def reset_offset(self):
        ''' resets and changes previosuly done using offset
        it implements UNDO feature be removing the last offset
		from the offset history.
        '''

        x_total = 0
        y_total = 0

        for x_offset, y_offset in self.offset_history:
            x_total += (x_offset * -1)
            y_total += (y_offset * -1)

        self.offset_history.clear()

        self.sample_offset(x_total, y_total)

    def sample_offset(self, x_offset, y_offset):
        ''' moves smaples +X and +Y pixels accorss the viewing window
        to correct fixation shift or other shifting problems manually

		x_offset : int
		offset to be applied on all fixations in the x axis

		y_offset : int
		offset to be applied on all fixations in the y axis

        '''

        # adding offsets to history
        self.offset_history.append((x_offset, y_offset))

        # go over all samples (SMPs) in trial data
        for sample in self.trial_data:

            # filter MSG samples if any exist, or R eye is inValid
            if sample[1] != "SMP" or sample[27] == "-1":
                continue

            # get x and y for each sample (right eye only)
            # [23] R POR X [px]	 '0.00',
            # [24] R POR Y [px]	 '0.00',
            x_cord, y_cord = float(sample[23]), float(sample[24])

            sample[23] = str(x_cord + x_offset)
            sample[24] = str(y_cord + y_offset)


class SMIRed250_Trial(Trial):
    def __init__(self, trial, participant, data, image):
        super().__init__(trial, participant, image)
        self.trial_data = [] + data


    def get_sample_number(self):
        ''' returns the number of samples in the trial '''
        return len(self.trial_data)


    def print_trial_data(self):
        ''' prints trial data '''
        return self.trial_data


    def filter_fixations(self, minimum_duration=50, sample_duration=4, maxmimum_dispersion=25):
        '''based on page 296 of eye tracker manual:
        https://psychologie.unibas.ch/fileadmin/user_upload/psychologie/Forschung/N-Lab/SMI_iView_X_Manual.pdf

		minimum_duration : int (optional)
		minimum duration for a fixation in milliseconds, less than minimum is considered noise.
		set to 50 milliseconds by default.

		sample_duration : int (optional)
		Sample duration in milliseconds, this is 4 milliseconds based on this eye tracker.

		maxmimum_dispersion : int (optional)
		maximum distance from a group of samples to be considered a single fixation.
		Set to 25 pixels by default.


        notes:
        remember that some data is MSG for mouse clicks.
        some records are invalid with value -1.
        read right eye data only.
        '''

        # clears fixations in case called multiple times
        self.fixations.clear()

        # create moving window based on minimum_duration
        window_size = int( math.ceil( minimum_duration / sample_duration ))

        window_x = []
        window_y = []

        # go over all SMPs in trial data
        for sample in self.trial_data:

            # filter MSG samples if any exist, or R eye is inValid
            if sample[1] != "SMP" or sample[27] == "-1":
                continue

            # get x and y for each sample (right eye only)
            # [23] R POR X [px]	 '0.00',
            # [24] R POR Y [px]	 '0.00',
            x_cord, y_cord = float(sample[23]), float(sample[24])

            # filter (skip) cordinates outside of the screen 1920×1080 px
            if x_cord < 0 or y_cord < 0 or x_cord > 1920 or y_cord > 1080:
                continue

            # adding sample if it appears to be valid
            window_x.append(x_cord)
            window_y.append(y_cord)

            # calculate dispersion = [max(x) - min(x)] + [max(y) - min(y)]
            dispersion = (max(window_x) - min(window_x)) + (max(window_y) - min(window_y))

            # if dispersion is above maxmimum_dispersion
            if dispersion > maxmimum_dispersion:

                # then the window does not represent a fixation
                # pop last item in window
                window_x.pop()
                window_y.pop()

                # add fixation to fixations if window is not empty (size >= window_size)
                if len(window_x) == len(window_y) and len(window_x) > window_size:

                    # print("duration", len(window_x)*4, "is average of", len(window_x), "samples")

                    # the fixation is registered at the centroid of the wondow points
                    # trial, participant, timestamp, duration, x_cord, y_cord, token
                    self.fixations.append( Fixation(self.trial_ID,
                                                    self.trial_participant,
                                                    sample[0],
                                                    len(window_x)*4,
                                                    statistics.mean(window_x),
                                                    statistics.mean(window_y),
                                                    "na"))

                # clear window
                window_x.clear()
                window_y.clear()

            # if dispersion is below maxmimum_dispersion
            # then the window represents a fixation
            # in this case the window expands to the right until
            # the wondow dispersion is above threshold


    def draw_trial(self, images_path, draw_raw_data, draw_filtered_fixations, path, save_image):
        '''draws the trial image and raw-data/fixations over the image
        circle size indicates fixation duration

		images_path : String
		path for trial image file.

		draw_raw_data : boolean
		whether user wants raw data drawn.

		draw_filtered_fixations : boolean
		Whether user wants filtered fixations drawn.

        path : String
        The path where the image will be saved.

        save_image : Boolean
        Whether the resulting image should be saved at "path" or not.
        '''

        trial_image = self.trial_image

        im = Image.open(images_path + trial_image)

        draw = ImageDraw.Draw(im)


        if draw_raw_data:
        	# draw raw data before fixation filter
            for fix in self.trial_data:

                # invalid records
                if len(fix) > 5:
                    x_cord = float(fix[23])
                    y_cord = float(fix[24]) #- 150

                dot_size = 5

                draw.ellipse((x_cord - (dot_size/2),
                			y_cord - (dot_size/2),
                			x_cord + dot_size, y_cord + dot_size),
                            fill=(255,0,0,0))

        if draw_filtered_fixations:

            # draw fixations
            for fix in self.fixations:

                # fixation coordinates on 1920×1080 px
                x_cord = fix.get_fixation()[4]
                y_cord = fix.get_fixation()[5]

                #circle size is 5
                dot_size = 5 #fix.get_fixation()[3]  # circle size is based on fixation duration

                draw.ellipse((x_cord-(dot_size/2),
                			y_cord-(dot_size/2),
                			x_cord+dot_size,
                			y_cord+dot_size),
                            fill=(0,255,0,0))


        plt.figure(figsize = (17,15))
        plt.imshow(np.asarray(im), interpolation='nearest')

        imshow(np.asarray(im))

        # if save_image is True, save image in path
        if save_image:
            # saves generated image with offset values applied
            image_name = path + \
                        str(self.trial_participant) +\
                        "-t" + \
                        str(self.trial_ID) +\
                        "-offsetx" + \
                        str(self.get_offset()[0]) +\
                        "y"+ \
                        str(self.get_offset()[1]) +\
                        ".png"

            plt.savefig(image_name)

            print(image_name, "saved!")


class EyeLink1000_Trial(Trial):
    def __init__(self, trial, participant, image, fixations, saccades, blinks):
        super().__init__(trial, participant, image)

        self.fixations = fixations
        # Eyelink1000
        self.saccades = saccades
        self.blinks = blinks


    def get_sample_number(self):
        ''' returns the number of samples in the trial '''
        return len(self.fixations.values()) + len(self.saccades.values()) + len(self.blinks.values())

    def get_fixations(self):
        ''' returns the filtered fixations in the trial '''
        return self.fixations.values()

    # [UPDATE] Add saccade and blink getter for EyeLink1000
    def get_saccade_number(self):
        ''' returns the number of saccades in the trial '''
        return len(self.saccades)


    def get_saccade(self):
        ''' returns the saccades in the trial '''
        return self.saccades.values()


    def get_blink_number(self):
        ''' returns the number of blinks in the trial '''
        return len(self.blinks)


    def get_blink(self):
        ''' returns the blinks in the trial '''
        return self.blinks.values()

    def draw_trial(self, images_path, save_image=False):
        trial_image = self.trial_image

        background_size = (1024,768)
        trial_location = (10, 375)

        img = Image.new('RGBA', background_size, color='black')
        foreground = Image.open(images_path + trial_image)

        img.paste(foreground, trial_location, foreground.convert('RGBA'))

        draw = ImageDraw.Draw(img)

        for count, fixation in self.fixations.items():
            duration = fixation.duration
            if 5 * (duration / 100) < 5:
                r = 3
            else:
                r = 5 * (duration / 100)

            x = fixation.x_cord
            y = fixation.y_cord

            bound = (x-r, y-r, x+r, y+r)
            outline_color = (255, 255, 0, 255)
            fill_color = (121, 128, 0, 255)
            draw.ellipse(bound, fill=fill_color, outline=outline_color)

            text_bound = (x, y-r/2)
            text_color = (255, 0, 0, 255)
            draw.text(text_bound, str(count), fill=text_color)

        for count, saccade in self.saccades.items():
            x = saccade.x_cord
            y = saccade.y_cord
            x1 = saccade.x1_cord
            y1 = saccade.y1_cord

            bound = (x, y, x1, y1)
            line_color = (122, 122, 0, 255)
            penwidth = 2
            draw.line(bound, fill=line_color, width=penwidth)

            text_bound = ((x+x1)/2, (y+y1)/2)
            text_color = (255, 0, 0, 255)
            draw.text(text_bound, str(count), fill=text_color)


        return img

class Experiment():
    '''each subject data represnets an experiment with multiple trials'''


    def __init__(self, tfile, eyetracker):
        ''' initialize each experiment with raw data file
        This method splits data into a bunch of trials based on JPG


        tfile: String
		raw data TSV file.

        eyetracker: String
        typle of eye tracker used
        '''

        if eyetracker == 'SMIRed250':
            self.parse_tsv(tfile)
        elif eyetracker == 'EyeLink1000':
            self.parse_asc(tfile)


    def parse_tsv(self, tfile):
        '''Parse SMIRed250's tsv file

        tfile : str
        name of the tsv file
        '''

        # reading raw data file from EMIP dataset
        tsv_file = open(tfile)
        print("parsing file:", tfile)

        self.trial = []

        text = tsv_file.read()

        text_lines = text.split('\n')

        active = False    # indicates whether samples are being recorded in trials
        # the goal is to skip metadata in the file

        trial_data = []
        trial_image = []

        for line in text_lines:

            token = line.split("\t")

            if active:
                trial_data.append(token)


            if len(token) < 3:
                continue

            if token[1] == "MSG" and token[3].find(".jpg") != -1:

                msg = token[3].split(' ')    # Message: vehicle_java2.jpg

                trial_image.append(msg)      # vehicle_java2.jpg

                if active:
                    # parse trial, participant, data, image

                    trial_ID = len(self.trial)
                    participant_ID = tfile.split('/')[-1].split('_')[0]

                    self.trial.append(SMIRed250_Trial(trial_ID,
                                            participant_ID,
                                            trial_data[:-1],
                                            trial_image[-2][-1]))

                    trial_data.clear()

                active = True

        # adds the last trial
        self.trial.append(SMIRed250_Trial(len(self.trial),
        						tfile.split('/')[-1][:3],
        						trial_data,
        						trial_image[-1][-1]))


    def parse_asc(self, tfile):
        '''Parse EyeLink1000's asc file

        tfile : str
        name of the asc file
        '''

        asc_file = open(tfile)
        print("parsing file:", tfile)

        self.trial = []

        text = asc_file.read()
        text_lines = text.split('\n')

        trial_ID = -1
        participant_ID = tfile.split('.')[0]

        # [UPDATE] Store in dictionary for order
        trial_fixations = {}
        trial_saccades = {}
        trial_blinks = {}

        count = 0

        for line in text_lines:

            token = line.split()

            if token == []:
                continue

            if "TRIALID" in token:
                # List of eye events
                if trial_ID == -1:
                    trial_ID = int(token[-1])
                    continue

                # Read image location
                index = str(int(trial_ID)+1)
                experiment = participant_ID.split('/')[-1]
                location = f'runtime/dataviewer/{experiment}/graphics/VC_{index}.vcl'
                with open(location, 'r') as file:
                    image = file.readlines()[1].split()[-3].split('/')[-1]

                # Append fixations and saccades list here
                self.trial.append(EyeLink1000_Trial(trial_ID,
                                                    participant_ID,
                                                    image, # [UPDATE] Add image
                                                    trial_fixations,
                                                    trial_saccades,
                                                    trial_blinks))
                # [UPDATE] Fix same reference issue
                trial_fixations = {}
                trial_saccades = {}
                trial_blinks = {}
                count = 0
                trial_ID = int(token[-1])

            if token[0] == "EFIX":
                timestamp = int(token[2])
                duration = int(token[4])
                x_cord = float(token[5])
                y_cord = float(token[6])
                pupil = int(token[7])

                trial_fixations[count] = EyeLink1000_Fixation(trial_ID,
                                                participant_ID,
                                                timestamp,
                                                duration,
                                                x_cord,
                                                y_cord,
                                                "", # Token Needed
                                                pupil)
                count += 1

            if token[0] == "ESACC":
                timestamp = int(token[2])
                duration = int(token[4])
                # [Question] "." Exist in asc file
                x_cord = float(token[5]) if token[5] != '.' else 0.0
                y_cord = float(token[6]) if token[6] != '.' else 0.0
                x1_cord = float(token[7]) if token[7] != '.' else 0.0
                y1_cord = float(token[8]) if token[8] != '.' else 0.0
                amplitude = float(token[9])
                peak_velocity = int(token[10])
                trial_saccades[count] = EyeLink1000_Saccade(trial_ID,
                                            participant_ID,
                                            timestamp,
                                            duration,
                                            x_cord,
                                            y_cord,
                                            x1_cord,
                                            y1_cord,
                                            amplitude,
                                            peak_velocity)
                count += 1

            if token[0] == "EBLINK":
                timestamp = int(token[2])
                duration = int(token[4])
                trial_blinks[count] = EyeLink1000_Blink(trial_ID,
                                                    participant_ID,
                                                    timestamp,
                                                    duration)
                count += 1

        # Read image location
        index = str(int(trial_ID)+1)
        experiment = participant_ID.split('/')[-1]
        location = f'runtime/dataviewer/{experiment}/graphics/VC_{index}.vcl'
        with open(location, 'r') as file:
            image = file.readlines()[1].split()[-3].split('/')[-1]
            image = f'runtime/images/{image}'

        # Add the last trial
        self.trial.append(EyeLink1000_Trial(trial_ID,
                                            participant_ID,
                                            image, # Image Needed
                                            trial_fixations,
                                            trial_saccades,
                                            trial_blinks))

        asc_file.close()
        trial_fixations = []
        trial_saccades = []
        trial_blinks = []


    def get_number_of_trials(self):
        '''returns the number of trials in the experiment'''
        return len(self.trial)


import pandas as pd

def find_rectangles(code_image, level="sub-line", margin_height=4, margin_width=7):
    ''' returns a dataframe with AOIs as rectangles with line and part number
    AOI x-coordinate, AOI y-coordinate, width, height, and image file name.

    code_image : String
    Code image file, e.g. "vehicle_scala.jpg"

    level = String
    the AOI level with two options "line" level each line is an AOI or
    "sub-line" level where each token is an AOI.

    margin_height : int
    the marginal height between line of code and boarder of the detecting rectangle

    margin_width : int
    the marginal width between token of code and boarder of the detecting rectangle
    '''

    img = Image.open(code_image).convert('1')

    width, height = img.size

    left, right = 0, width

    vertical_result, upper_bounds, lower_bounds = [], [], []

    # Move the detecting rectangle from the top to the buttom of the image
    for upper in range(height - margin_height):

        lower = upper + margin_height

        box = (left, upper, right, lower)
        minimum, maximum = img.crop(box).getextrema()

        if upper > 1:
            if vertical_result[-1][2] == 255 and minimum == 0:
                # Rectangle detects black color for the first time in a while -> Start of one line
                upper_bounds.append(upper)
            if vertical_result[-1][2] == 0 and minimum == 255:
                # Rectangle detects white color for the first time in a while -> End of one line
                lower_bounds.append(lower)

        # Storing all detection result
        vertical_result.append([upper, lower, minimum, maximum])


    final_result = []

    line_count = 1

    # Iterate through each line of code from detection
    for upper_bound, lower_bound in list(zip(upper_bounds, lower_bounds)):

        # Reset all temporary result for the next line
        horizontal_result, left_bounds, right_bounds = [], [], []

        # Move the detecting rectangle from the left to the right of the image
        for left in range(width - margin_width):

            right = left + margin_width

            box = (left, upper_bound, right, lower_bound)
            minimum, maximum = img.crop(box).getextrema()

            if left > 1:
                if horizontal_result[-1][2] == 255 and minimum == 0:
                    # Rectangle detects black color for the first time in a while -> Start of one word
                    left_bounds.append(left)
                if horizontal_result[-1][2] == 0 and minimum == 255:
                    # Rectangle detects white color for the first time in a while -> End of one word
                    right_bounds.append(right)

            # Storing all detection result
            horizontal_result.append([left, right, minimum, maximum])

        if level == 'sub-line':

            part_count = 1

            for left, right in list(zip(left_bounds, right_bounds)):
                final_result.append(['sub-line', f'line {line_count} part {part_count}', left, upper_bound, right, lower_bound])
                part_count += 1

        elif level == 'line':
            final_result.append(['line', f'line {line_count}', left_bounds[0], up, right_bounds[-1], low])

        line_count += 1

    # Format pandas dataframe
    columns = ['kind', 'name', 'x', 'y', 'width', 'height', 'local_id', 'image']
    aoi_df = pd.DataFrame(columns=columns)

    for entry in final_result:
        kind, name, x, y, x0, y0 = entry
        width = x0 - x
        height = y0 - y
        local_id = np.nan
        image = code_image

        # For better rectangles
        x += margin_width / 2
        width -= margin_width

        value = [kind, name, x, y, width, height, local_id, image]
        dic = dict(zip(columns, value))

        aoi_df = aoi_df.append(dic, ignore_index=True)

    return aoi_df

from PIL import ImageEnhance


def draw_rectangles(aoi_rectangles, code_image):
    ''' Draws AOI rectangles on to an image.

    aoi_rectangles : Pandas Dataframe
	dataframe containing recentagles representing areas of interest (AOIs)

    code_image : PIL image
    image on which AOI rectangles will be imposed
    '''

    # copy original image
    rect_image = code_image.copy()
    draw = ImageDraw.Draw(rect_image)

    # loop over rectangles and draw them
    for row in aoi_rectangles.iterrows():
        x_cordinate = row[1]['x']
        y_cordinate = row[1]['y']
        height = row[1]['height']
        width = row[1]['width']
        draw.rectangle([(x_cordinate, y_cordinate),
                        (x_cordinate + width - 1, y_cordinate + height - 1)],
                        outline = "#000000")

    return rect_image


def add_tokens_to_AOIs(file_path, aois_raw):
    ''' Adds tokens from code files to aois dataframe and returns it.

	file_path : String
	path to directory where code files are stored. In EMIP this is "emip_stimulus_programs"

	aois_raw : Pandas Dataframe
	the dataframe where AOIs are stored.
    '''

    image_name = aois_raw["image"][1]

    # rectangle files
    if image_name == "rectangle_java.jpg":
        file_name = "Rectangle.java"

    if image_name == "rectangle_java2.jpg":
        file_name = "Rectangle.java"

    if image_name == "rectangle_python.jpg":
        file_name = "Rectangle.py"

    if image_name == "rectangle_scala.jpg":
        file_name = "Rectangle.scala"

    # vehicle files
    if image_name == "vehicle_java.jpg":
        file_name = "Vehicle.java"

    if image_name == "vehicle_java2.jpg":
        file_name = "Vehicle.java"

    if image_name == "vehicle_python.jpg":
        file_name = "vehicle.py"

    if image_name == "vehicle_scala.jpg":
        file_name = "Vehicle.scala"

    code_file = open(file_path + file_name)

    code_text = code_file.read()

    code_line = code_text.replace('\t','').replace('        ','').replace('    ','').split('\n')

    filtered_line = []

    for line in code_line:
        if len(line) != 0:
            filtered_line.append(line.split(' '))

    # after the code file has been tokenized and indexed
    # we can attach tokens to correct AOI

    aois_raw = aois_raw[aois_raw.kind == "sub-line"].copy()

    tokens = []

    for location in aois_raw["name"].iteritems():

        line_part = location[1].split(' ')
        line_num = int(line_part[1])
        part_num = int(line_part[3])

        #print(line_part, filtered_line[line_num - 1])
        tokens.append(filtered_line[line_num - 1][part_num -1])

    aois_raw["token"] = tokens

    if aois_raw[aois_raw['token'] == '']['name'].count() != 0:
        print("Error in adding tokens, some tokens are missing!")

    return aois_raw



def add_srcml_to_AOIs( aois_raw):
    ''' Adds srcML tags to aois dataframe and returns it.
    Check https://www.srcml.org/ for more information about srcML

	The files: rectangle.tsv and vehicle.tsv should be in the same directory as the code.


	aois_raw : Pandas Dataframe
	the dataframe where AOIs are stored.
    '''

    image_name = aois_raw["image"][1]

    #SRCML rectangle files
    if image_name == "rectangle_java.jpg":
        file_name = "rectangle.tsv"

    if image_name == "rectangle_java2.jpg":
        file_name = "rectangle.tsv"

    if image_name == "rectangle_python.jpg":
        aois_raw["srcML_tag"] = 'na'
        return aois_raw

    if image_name == "rectangle_scala.jpg":
        aois_raw["srcML_tag"] = 'na'
        return aois_raw

    #SRCML vehicle files
    if image_name == "vehicle_java.jpg":
        file_name = "vehicle.tsv"

    if image_name == "vehicle_java2.jpg":
        file_name = "vehicle.tsv"

    if image_name == "vehicle_python.jpg":
        aois_raw["srcML_tag"] = 'na'
        return aois_raw

    if image_name == "vehicle_scala.jpg":
        aois_raw["srcML_tag"] = 'na'
        return aois_raw

    srcML_table = pandas.read_csv(file_name, sep='\t')

    aois_raw = aois_raw[aois_raw.kind == "sub-line"].copy()

    #after the srcML file has been recognized
    #we can attach tokens to correct AOI

    tags = []

    for location in aois_raw["name"].iteritems():
        found = False

        for srcML_row in srcML_table.itertuples(index=True, name='Pandas'):
            # stimulus_file	token	AOI	syntactic_context

            if srcML_row.AOI == location[1]:
                tags.append(srcML_row.syntactic_context)
                found = True

        if not found:
            tags.append("na")

    aois_raw["srcML_tag"] = tags

    return aois_raw




def overlap(fix, AOI, radius=25):
    '''
    checks if fixation is within radius distance or over an AOI. Returns True/False.

	fix : Fixation
	A single fixation in a trial being considered for overlapping with the AOI.

	AOI : Pandas dataframe row
	contains AOI #kind	name	x	y	width	height	local_id	image	token

	radius : int (optional)
	radius around AOI to consider fixations in it within the AOI.
	default is 25 pixles since the fixation filter groups samples within 25 pixles.

    '''

    box_x = AOI.x - (radius / 2)
    box_y = AOI.y - (radius / 2)
    box_w = AOI.width + (radius / 2)
    box_h = AOI.height + (radius / 2)

    if fix.x_cord >= box_x and fix.x_cord <= box_x + box_w \
    and fix.y_cord >= box_y and fix.y_cord <= box_y + box_h:
        return True

    else:

        return False


def hit_test(trial, aois_tokens, radius = 25 ):
    '''
    checks if fixations are within AOI with a fixation radius of 25 px
    (since each fix is a sum of samples within 25px)

    trial : Trial
    contains fixations and other metadata (trial#, participant, code_file, code_language)
             - fixation includes timestamp, duration, x_cord, y_cord

    aois_with_tokens : Pandas Dataframe
    contains each AOI location and dimentions and token text

    return : pandas dataframe with a record representing each fixation, each record contains:
    trial, participant, code_file, code_language, timestamp, duration, x_cord, y_cord, token, length
    '''

    header = ["trial",
			  "participant",
			  "code_file",
			  "code_language",
			  "timestamp",
			  "duration",
			  "x_cord",
			  "y_cord",
			  "aoi_x",
			  "aoi_y",
			  "aoi_width",
			  "aoi_height",
			  "token",
			  "length",
			  "srcML"]

    result = pandas.DataFrame(columns=header)
    print("all fixations:", len(trial.get_fixations()))

    for fix in trial.get_fixations():

        for row  in aois_tokens.itertuples(index=True, name='Pandas'):
            #kind	name	x	y	width	height	local_id	image	token

            if overlap(fix, row, radius):
                df = pandas.DataFrame([[fix.trial_ID,
                                        fix.participant,
                                        row.image,
                                        row.image,
                                        fix.timestamp,
                                        fix.duration,
                                        fix.x_cord,
                                        fix.y_cord,
                                        row.x,
                                        row.y,
                                        row.width,
                                        row.height,
                                        row.token,
                                        len(row.token),
                                        row.srcML_tag],], columns=header)

                result = result.append(df, ignore_index=True)

    return result


def EMIP_dataset(path, sample_size = 216, eyetracker='SMIRed250'):
    '''

    path : String
    path to EMIP dataset rawdata directory, example '../../emip_dataset/rawdata/'

    sample_size : Int (optional)
    The number of subjects to be processed, the default is 216

    return : Dictionary
    dictionary of experiments where the key is the subject ID

    '''

    import os

    subject = {}
    count = 0

    # go over .tsv files in the rawdata dicrectory add files and count them
    # r=root, d=directories, f = files
    for r, d, f in os.walk(path):
        for file in f:
            if '.tsv' in file:

                participant_ID = file.split('/')[-1].split('_')[0]

                if subject.get(participant_ID, -1) == -1:
                    subject[participant_ID] = Experiment(tfile=os.path.join(r, file), eyetracker=eyetracker)
                else:
                    print("Error, experiment already in dictionary")

            if '.asc' in file:

                participant_ID = file.split('.')[0]

                if subject.get(participant_ID, -1) == -1:
                    subject[participant_ID] = Experiment(tfile=os.path.join(r, file), eyetracker=eyetracker)
                else:
                    print("Error, experiment already in dictionary")

            count += 1

            # breaks after sample_size
            if count == sample_size:
                break

    return subject