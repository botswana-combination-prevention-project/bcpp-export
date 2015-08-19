from django.core.exceptions import MultipleObjectsReturned


class DenormalizeMixin(object):
    def denormalize(self, attr_suffix, fieldattrs, instance=None,
                    lookup_model=None, lookup_instance=None, lookup_string=None):
        """Denormalizes one or more instance attributes and adds the survey_abbrev suffix.

        This denormalize or flattens the values relative to a survey. If this method is called
        in a loop on Survey for surveys [Y1, Y2, Y3] an attribute name 'example_attribute' would
        be set as example_attribute_y1, example_attribute_y2, example_attribute_y3.

        For example::
            attr_suffix = suffix to add to an attr name that the data is denormalized on
            fieldattrs = [('report_datetime', 'member_absent_date'),
                          ('absent', 'member_absent')]
            for survey in Survey.objects.all():
                attr_suffix = survey.survey_abbrev
                subject_absentee_entry = self.denormalize((
                    attr_suffix, fieldattrs,
                    lookup_model=SubjectAbsenteeEntry
                    lookup_string='subject_absentee__household_member',
                    lookup_instance=self.household_membership_survey.get(survey.survey_slug)
                    )

        >>> dir(self)
        [ ...,
        member_absent_y1, member_absent_y3, member_absent_y3,
        ...,
        member_absent_date_y1, member_absent_date_y2, member_absent_date_y3,
        ...]
        """
        obj = None
        lookup_flds = {}
        for fldname, attrname in fieldattrs:
            # set attribute on self to None
            attrname = '{}_{}'.format(attrname, attr_suffix.lower())
            setattr(self, attrname, None)
            try:
                # try to set value from instance
                field_value = getattr(instance, fldname)
                setattr(self, attrname, field_value)
            except AttributeError:
                if lookup_model:
                    # collect fields/attrs for query below
                    lookup_flds.update({fldname: attrname})
        if lookup_flds:
            try:
                values = lookup_model.objects.values(
                    *lookup_flds).get(
                    **{lookup_string: lookup_instance})
                for fld, value in values.iteritems():
                    setattr(self, lookup_flds[fld], value)
            except lookup_model.DoesNotExist:
                for attr in lookup_flds.values():
                    setattr(self, attr, None)
            except MultipleObjectsReturned:
                values_queryset = lookup_model.objects.values(
                    *lookup_flds).filter(
                    **{lookup_string: lookup_instance})
                for values in values_queryset:
                    vals = {fld: [] for fld in values}
                    for fld, value in values.iteritems():
                        vals[fld].append(value)
                    for fld in values:
                        setattr(self, lookup_flds[fld], vals[fld])
        return obj

    def denormalize_other(self, attr_suffix, fieldattrs, instance):
        """Adds denormalized attrs to self from "Other Specify ..." fields

        If the value of attr 'fldname' is 'OTHER' uses the value of 'other_fldname'."""
        for fldname, other_fldname, attrname in fieldattrs:
            attrname = '{}_{}'.format(attrname, attr_suffix.lower())
            try:
                if getattr(instance, fldname) == 'OTHER':
                    field_value = getattr(instance, other_fldname)
                else:
                    field_value = getattr(instance, fldname)
                setattr(self, attrname, field_value)
            except AttributeError:
                setattr(self, attrname, None)

    def normalize(self, instance, attrname, attr_suffix_list):
        values = []
        for attr_suffix in attr_suffix_list:
            print getattr(instance, '{}_{}'.format(attrname, attr_suffix))
            values.append(getattr(instance, '{}_{}'.format(attrname, attr_suffix)))
        return values
