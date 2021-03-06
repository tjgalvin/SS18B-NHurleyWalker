"""
Distributed under the MIT License. See LICENSE.txt for more info.
"""

from django.db import models
from django.utils import timezone

from . import constants


class SearchPage(models.Model):
    """
    Search Page to define search on various database tables
    """

    # name of the search page
    name = models.CharField(max_length=255, null=False, blank=False, unique=True)

    # display title on the search page
    display_name = models.CharField(max_length=255, null=False, blank=False, unique=True)

    # order to define in which order this would be displayed in the menu
    display_order = models.SmallIntegerField(unique=True, null=False, blank=False)

    # marks whether active or not
    active = models.BooleanField(default=True, null=False, blank=False)

    def __str__(self):
        return '{display_order}. {display_name} ({active})'.format(
            display_order=self.display_order,
            display_name=self.display_name,
            active='Active' if self.active else 'Inactive'
        )


class SearchInputGroup(models.Model):
    """
    input group to categorise search inputs
    """

    # name of the input group
    name = models.CharField(max_length=255, null=False, blank=False, unique=True)

    # input group name to store the display title. ex: Search Parameters, Time Constraints, etc.
    display_name = models.CharField(max_length=255, null=False, blank=False)

    # just to store information about the input group to render in the UI template
    description = models.TextField(null=True, blank=True)

    # order to define in which order this group would be displayed
    display_order = models.SmallIntegerField(unique=True, null=False, blank=False)

    # marks whether the input group is active or not
    active = models.BooleanField(default=True, null=False, blank=False)

    def __str__(self):
        return '{display_order}. {display_name} ({active})'.format(
            display_order=self.display_order,
            display_name=self.display_name,
            active='Active' if self.active else 'Inactive'
        )


class SearchInput(models.Model):
    """
    input to filter the search results
    """

    # determines under which group the input will be rendered,
    # null = True would put it to others, however that is not currently the case, therefore, no search input
    # can be present without a group.
    search_input_group = models.ForeignKey(SearchInputGroup, on_delete=models.CASCADE, null=False, blank=False)

    # name of the input
    name = models.CharField(max_length=255, null=False, blank=False)

    # display name to show in the template
    display_name = models.CharField(max_length=255, null=False, blank=False)

    # to appear as help text or can be used for extra description for checkboxes
    input_info = models.TextField(null=True, blank=True,
                                  help_text='For multiple inputs(ex: RADIUS) use #$# as separators.')

    # table name in the actual database for searching
    table_name = models.CharField(max_length=255, null=False, blank=False)

    # field name in the table in the actual database for searching
    field_name = models.CharField(max_length=255, null=False, blank=False)

    # field types that are used in the database
    INT = 'Integer'
    TEXT = 'Text'
    FLOAT = 'Float'
    BOOL = 'Bool'
    TEXTTIME = 'Text(Time)'

    # field type choices
    FIELD_TYPE_CHOICES = [
        (INT, INT),
        (TEXT, TEXT),
        (FLOAT, FLOAT),
        (BOOL, BOOL),
        (TEXTTIME, TEXTTIME),
    ]

    # field type in the actual database for searching
    field_type = models.CharField(max_length=50, choices=FIELD_TYPE_CHOICES, blank=False, null=False, default=TEXT)

    # input type choices
    INPUT_TYPE_CHOICES = [
        (constants.TEXT, constants.TEXT_DISPLAY),
        (constants.NUMBER, constants.NUMBER_DISPLAY),
        (constants.MIN_NUMBER, constants.MIN_NUMBER_DISPLAY),
        (constants.MAX_NUMBER, constants.MAX_NUMBER_DISPLAY),
        (constants.MAX_ABSOLUTE_NUMBER, constants.MAX_ABSOLUTE_NUMBER_DISPLAY),
        (constants.CHECKBOX, constants.CHECKBOX_DISPLAY),
        (constants.RADIUS, constants.RADIUS_DISPLAY),
        (constants.RANGE, constants.RANGE_DISPLAY),
        (constants.RANGE_INT, constants.RANGE_INT_DISPLAY),
        (constants.RANGE_NON_NEG_INT, constants.RANGE_NON_NEG_INT_DISPLAY),
        (constants.SELECT, constants.SELECT_DISPLAY),
        (constants.DATE_GPS, constants.DATE_GPS_DISPLAY),
        (constants.DATE_GPS_RANGE, constants.DATE_GPS_RANGE_DISPLAY),
        (constants.DATE_UNIX, constants.DATE_UNIX_DISPLAY),
        (constants.DATE_UNIX_RANGE, constants.DATE_UNIX_RANGE_DISPLAY),
    ]

    # input type to define how the input will be rendered in the UI
    input_type = models.CharField(max_length=50, choices=INPUT_TYPE_CHOICES, blank=False, null=False, default=TEXT)

    # initial value to be rendered in the input field
    initial_value = models.CharField(max_length=255, blank=True, null=True)

    # placeholder for the UI
    placeholder = models.CharField(max_length=255, blank=True, null=True)

    # is the input required?
    required = models.BooleanField(default=False, null=False, blank=False)

    # order to define in which order this input would be displayed
    display_order = models.SmallIntegerField(null=False, blank=False)

    # marks whether the input is active or not
    active = models.BooleanField(default=True, null=False, blank=False)

    class Meta:
        unique_together = (
            ('search_input_group', 'name',),
            ('search_input_group', 'display_order',),
        )

    def __str__(self):
        return '{display_order}. {display_name} ({active})'.format(
            display_order=self.display_order,
            display_name=self.display_name,
            active='Active' if self.active else 'Inactive'
        )

    @property
    def initial_value_adjusted(self):
        """
        This defines the initial value for a search input. For multiple and dependent inputs, we need to recalculate
        the initial values. For example, for a range input, initial values are stored in initial_value as a comma-
        separated one. If it is a,b: then first input would have the initial value of a and second one would have b.
        This is also used to interpret the human readable strings to actual values like 'today' to be converted to
        an actual date for date type fields.
        :return: initial value for the search input
        """
        now = timezone.localtime(timezone.now()).strftime('%d/%m/%Y')

        if self.input_type in [constants.DATE_GPS, constants.DATE_UNIX]:
            if self.initial_value.lower() == 'today':
                return now

        elif self.input_type in [constants.RANGE, constants.RANGE_INT, constants.RANGE_NON_NEG_INT]:
            initial_values = ['', '']
            try:
                parts = self.initial_value.split(',')
            except AttributeError:
                return initial_values

            for index, part in enumerate(parts):
                initial_values.insert(index, part.strip())

            return initial_values

        elif self.input_type == constants.RADIUS:
            initial_values = ['', '']
            try:
                parts = self.initial_value.split(',')
            except AttributeError:
                return initial_values

            for index, part in enumerate(parts):
                initial_values.insert(index, part.strip())

            return initial_values

        elif self.input_type in [constants.DATE_GPS_RANGE, constants.DATE_UNIX_RANGE]:
            initial_values = ['', '']
            try:
                parts = self.initial_value.split(',')
            except AttributeError:
                return initial_values

            for index, part in enumerate(parts):
                if part.strip().lower() == 'today':
                    initial_values.insert(index, now)
                else:
                    initial_values.insert(index, part.strip())

            return initial_values

        return self.initial_value

    @property
    def help_text_adjusted(self):
        """
        Finds the help text for multiple inputs. For multiple inputs help-text can be in one line separated by #$#.
        This function splits the help text and forms an array for those inputs and returns it so that help texts can be
        displayed in the UI properly. This also means that, for multiple inputs, we can have different help texts for
        different inputs.
        :return: array of help text or string of help text.
        """

        if self.input_type in [
            constants.RANGE,
            constants.RANGE_INT,
            constants.RANGE_NON_NEG_INT,
            constants.RADIUS,
            constants.DATE_GPS_RANGE,
            constants.DATE_UNIX_RANGE,
        ]:

            help_texts = ['', '']

            try:
                parts = self.input_info.split('#$#')
            except AttributeError:
                return help_texts

            for index, part in enumerate(parts):
                help_texts.insert(index, part.strip())

            return help_texts
        else:
            return self.input_info.strip()


class SearchInputOption(models.Model):
    """
    Choice inputs for fields like Select and Radio
    """

    # search input
    search_input = models.ForeignKey(SearchInput, on_delete=models.CASCADE, blank=False, null=False)

    # option name (value in UI)
    name = models.CharField(max_length=255, blank=False, null=False)

    # option display to show in UI
    display_name = models.CharField(max_length=255, blank=False, null=False)

    # order to define in which order this input option would be displayed
    display_order = models.SmallIntegerField(null=False, blank=False)

    # marks whether the input is active or not
    active = models.BooleanField(default=True, null=False, blank=False)

    class Meta:
        unique_together = (
            ('search_input', 'name',),
            ('search_input', 'display_order',),
        )

    def __str__(self):
        return '{display_order}. {display_name} ({active})'.format(
            display_order=self.display_order,
            display_name=self.display_name,
            active='Active' if self.active else 'Inactive'
        )


class SearchPageInputGroup(models.Model):
    """
    Defines which input groups will be present on which search page
    """

    # search page
    search_page = models.ForeignKey(SearchPage, on_delete=models.CASCADE, blank=False, null=False, )

    # search input group
    search_input_group = models.ForeignKey(SearchInputGroup, on_delete=models.CASCADE, blank=False, null=False, )

    # marks whether active or not
    active = models.BooleanField(default=True, null=False, blank=False)

    class Meta:
        unique_together = (
            ('search_page', 'search_input_group',),
        )

    def __str__(self):
        return '{search_page}. {search_input_group} ({active})'.format(
            search_page=self.search_page,
            search_input_group=self.search_input_group,
            active='Active' if self.active else 'Inactive'
        )


class SearchPageDisplayColumn(models.Model):
    """
    Defines which field columns are to be shown in the result page
    """

    # search page
    search_page = models.ForeignKey(SearchPage, on_delete=models.CASCADE, blank=False, null=False, )

    # table name in the actual database for searching
    table_name = models.CharField(max_length=255, null=False, blank=False)

    # field name in the table in the actual database for searching
    field_name = models.CharField(max_length=255, null=False, blank=False)

    # display name that is shown in the UI for this field
    display_name = models.CharField(max_length=255, null=False, blank=False)

    # order to define in which order this input option would be displayed
    display_order = models.SmallIntegerField(null=False, blank=False)

    # marks whether active or not
    active = models.BooleanField(default=True, null=False, blank=False)

    class Meta:
        unique_together = (
            ('search_page', 'table_name', 'field_name',),
            ('search_page', 'display_order',),
        )

    def __str__(self):
        return '{search_page}. {table_name}.{field_name} ({active})'.format(
            search_page=self.search_page,
            table_name=self.table_name,
            field_name=self.field_name,
            active='Active' if self.active else 'Inactive'
        )


class Colour(models.Model):
    """
    Defines colour and corresponding codes, required for sky-plots.
    """

    # name
    name = models.CharField(max_length=255, null=False, blank=False, unique=True)

    # hexadecimal code for the colour
    code = models.CharField(max_length=6, null=False, blank=False)

    class Meta:
        unique_together = (
            ('name', 'code',)
        )

    def __str__(self):
        return '{}({})'.format(self.name, self.code)


class SkyPlotsConfiguration(models.Model):
    """
    Configures the sky plots generation
    """

    # observation status entry, must be present in the observation table
    observation_status = models.CharField(max_length=255, null=False, blank=False, unique=True)

    # colour for the status
    colour = models.ForeignKey(Colour, on_delete=models.CASCADE, null=False, blank=True)

    def __str__(self):
        return '{} - {}'.format(self.observation_status, self.colour)


class SkyPlot(models.Model):
    """
    Storage for sky plots
    """

    # actual image name for the sky-plot. it may be a sub-path to static
    name = models.CharField(max_length=255, null=False, blank=False)

    # generation time of the sky-plot.
    generation_time = models.DateTimeField(null=False, blank=False, auto_now_add=True)

    # defines which sky-plot would be shown at the beginning.
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return '{} ({})'.format(self.name, self.generation_time) + ' :: default' if self.is_default else ''
