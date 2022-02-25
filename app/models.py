from django.contrib.postgres.fields import ArrayField
from django.db import models
from django import forms


class Employee(models.Model):
    name = models.CharField(max_length=254)
    team = models.ForeignKey('Team', on_delete=models.CASCADE)


class Department(models.Model):
    name = models.CharField(max_length=254)

    class Meta:
        ordering = ['name']

    @property
    def get_company(self):
        try:
            company = self.name.split('-')[0].strip()
        except:
            company = self.name
        return company

    @property
    def get_name(self):
        try:
            name = self.name.split('-')[1].strip()
        except:
            name = self.name
        return name


class Team(models.Model):
    name = models.CharField(max_length=254)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)

    class Meta:
        ordering = ['name']

    @property
    def get_company(self):
        try:
            company = self.name.split('-')[0].strip()
        except:
            company = self.name
        return company

    @property
    def get_name(self):
        try:
            name = self.name.split('-')[1].strip()
        except:
            name = self.name
        return name

    @property
    def get_city(self):
        try:
            city = self.name.split('-')[2].strip()
        except:
            city = self.name
        return city


class ChoiceArrayField(ArrayField):
    def formfield(self, **kwargs):
        defaults = {
            'form_class': forms.MultipleChoiceField,
            'choices': self.base_field.choices,
        }
        defaults.update(kwargs)
        return super(ArrayField, self).formfield(**defaults)


def dep_choices(n):
    choices = [(dep.name.split('-')[n].strip(), dep.name.split('-')[n].strip())
               for dep in Department.objects.all()]
    return sorted([t for t in (set(tuple(i) for i in choices))])


def team_choices(n):
    choices = []
    for dep in Team.objects.all():
        try:
            choices.append((dep.name.split('-')[n].strip(), dep.name.split('-')[n].strip()))
        except:
            pass
    return sorted([t for t in (set(tuple(i) for i in choices))])


class TelegramGroup(models.Model):
    CHOICES = [('or', 'OR'), ('not', 'NOT'), ('and', 'AND')]
    name = models.CharField(max_length=100)
    chat_id = models.BigIntegerField()
    department = ChoiceArrayField(models.CharField(choices=dep_choices(1),
                                                   max_length=254),
                                  default=list,
                                  help_text="Leave empty for all",
                                  blank=True)
    team_filter = models.CharField(max_length=10, choices=CHOICES, default='and', verbose_name='filter')
    team = ChoiceArrayField(models.CharField(choices=team_choices(1),
                                             max_length=254),
                            default=list,
                            help_text="Leave empty for all",
                            blank=True)
    city_filter = models.CharField(max_length=10, choices=CHOICES, default='and', verbose_name='filter')
    city = ChoiceArrayField(models.CharField(choices=team_choices(2),
                                             max_length=254),
                            default=list,
                            help_text="Leave empty for all",
                            blank=True)
    company_filter = models.CharField(max_length=10, choices=CHOICES, default='and', verbose_name='filter')
    company = ChoiceArrayField(models.CharField(choices=team_choices(0),
                                                max_length=254),
                               default=list,
                               help_text="Leave empty for all",
                               blank=True)
    active = models.BooleanField(default=True)
    extra_time = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Shift(models.Model):
    name = models.CharField(max_length=254)
    periods = ArrayField(models.IntegerField(), blank=True)


class Journey(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    interval = models.IntegerField()
    missing = models.IntegerField()
    normal = models.IntegerField()
    h1 = models.IntegerField()
    h2 = models.IntegerField()
    h3 = models.IntegerField()
    h4 = models.IntegerField()
    total_time = models.IntegerField()
    missing_days = models.IntegerField()
    proposals = models.IntegerField()
    dt = models.DateTimeField()


class History(models.Model):
    name = models.CharField(max_length=254)
    index = models.CharField(max_length=254)
    date_time = models.DateTimeField()

    class Meta:
        unique_together = ['name', 'date_time']
