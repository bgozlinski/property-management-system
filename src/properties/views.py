from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import Http404
from django.views.generic import CreateView, UpdateView, DeleteView, ListView
from .models import Property, Building, Unit, Equipment, Meter
from users.models import CustomUser
from .forms import PropertyForm, BuildingForm, UnitForm, EquipmentForm, MeterForm
from notifications.views import LandlordRequiredMixin


"""
This module provides views for property management in the system.

It includes views for creating, updating, deleting, listing, and viewing
property details, with appropriate access controls for landlords.
"""


class PropertyCreateView(LoginRequiredMixin, LandlordRequiredMixin, CreateView):
    """
    View for creating a new property.

    Only landlords can create properties. The property is automatically
    associated with the current user's landlord profile.
    """

    model = Property
    form_class = PropertyForm
    template_name = "add_property.html"
    success_url = reverse_lazy("profile")

    def form_valid(self, form):
        """
        Process the valid form and associate the property with the landlord.

        Args:
            form: The validated property form.

        Returns:
            HttpResponse: Redirect to the success URL with a success message.
        """
        form.instance.landlord = self.request.user.landlord
        response = super().form_valid(form)
        messages.success(self.request, "Property created successfully.")
        return response


class PropertyUpdateView(LoginRequiredMixin, LandlordRequiredMixin, UpdateView):
    """
    View for updating an existing property.

    Only landlords can update their own properties. Access is restricted
    to the property owner.
    """

    model = Property
    form_class = PropertyForm
    template_name = "property_detail.html"
    success_url = reverse_lazy("profile")

    def get_object(self, queryset=None):
        """
        Retrieve the property and verify ownership.

        Ensures that only the landlord who owns the property can update it.

        Args:
            queryset: Optional queryset to use for retrieving the object.

        Returns:
            Property: The property object if the user is the owner.

        Raises:
            Http404: If the user is not the owner of the property.
        """
        property_obj = super().get_object(queryset)
        if property_obj.landlord.user != self.request.user:
            raise Http404("Property not found")
        return property_obj

    def form_valid(self, form):
        """
        Process the valid form and save the updated property.

        Args:
            form: The validated property form.

        Returns:
            HttpResponse: Redirect to the success URL with a success message.
        """
        response = super().form_valid(form)
        messages.success(self.request, "Property updated successfully.")
        return response


class PropertyDeleteView(LoginRequiredMixin, LandlordRequiredMixin, DeleteView):
    """
    View for deleting an existing property.

    Only landlords can delete their own properties. Access is restricted
    to the property owner.
    """

    model = Property
    success_url = reverse_lazy("profile")

    def get(self, request, *args, **kwargs):
        """
        Handle GET requests by redirecting to POST.

        This prevents showing a confirmation page and directly processes
        the deletion when accessed via GET.

        Args:
            request: The HTTP request.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            HttpResponse: The result of the POST method.
        """
        return self.post(request, *args, **kwargs)

    def get_object(self, queryset=None):
        """
        Retrieve the property and verify ownership.

        Ensures that only the landlord who owns the property can delete it.

        Args:
            queryset: Optional queryset to use for retrieving the object.

        Returns:
            Property: The property object if the user is the owner.

        Raises:
            Http404: If the user is not the owner of the property.
        """
        property_obj = super().get_object(queryset)
        if property_obj.landlord.user != self.request.user:
            raise Http404("Property not found")
        return property_obj

    def delete(self, request, *args, **kwargs):
        """
        Delete the property and show a success message.

        Args:
            request: The HTTP request.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            HttpResponse: Redirect to the success URL with a success message.
        """
        messages.success(request, "Property deleted successfully.")
        return super().delete(request, *args, **kwargs)


class PropertyListView(LoginRequiredMixin, LandlordRequiredMixin, ListView):
    """
    View for listing properties owned by the current landlord.

    Property creation is disabled here per requirements; use dedicated forms
    for Buildings/Units/Equipment/Meters instead.

    Additionally, this view aggregates and exposes Buildings, Units, Equipment,
    and Meters related to the current landlord so the Properties page can
    display a consolidated overview.
    """

    model = Property
    template_name = "property_list.html"
    context_object_name = "properties"

    def get_queryset(self):
        return Property.objects.filter(landlord__user=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        landlord = self.request.user.landlord

        buildings = (
            Building.objects
            .filter(landlord=landlord)
            .order_by("name")
        )
        units = (
            Unit.objects
            .filter(building__landlord=landlord)
            .select_related("building")
            .order_by("building__name", "number")
        )
        equipment = (
            Equipment.objects
            .filter(unit__building__landlord=landlord)
            .select_related("unit", "unit__building")
            .order_by("unit__building__name", "unit__number", "name")
        )
        meters = (
            Meter.objects
            .filter(unit__building__landlord=landlord)
            .select_related("unit", "unit__building")
            .order_by("unit__building__name", "unit__number", "meter_type")
        )

        # Modal forms for Adds
        from .forms import BuildingForm, UnitForm
        building_form = BuildingForm()
        unit_form = UnitForm()
        unit_form.fields["building"].queryset = Building.objects.filter(landlord=landlord)

        ctx.update(
            {
                "buildings": buildings,
                "units": units,
                "equipment": equipment,
                "meters": meters,
                "buildings_count": buildings.count(),
                "units_count": units.count(),
                "equipment_count": equipment.count(),
                "meters_count": meters.count(),
                "building_form": building_form,
                "unit_form": unit_form,
            }
        )
        return ctx


class PropertyDetailView(LoginRequiredMixin, UpdateView):
    """
    View for displaying and updating property details.

    This view allows landlords to view and update their own properties.
    Administrators can also view and update any property.
    """

    model = Property
    form_class = PropertyForm
    template_name = "property_detail.html"
    success_url = reverse_lazy("property_list")

    def get_object(self, queryset=None):
        """
        Retrieve the property and verify access permissions.

        Ensures that only the landlord who owns the property or an administrator
        can view and update it.

        Args:
            queryset: Optional queryset to use for retrieving the object.

        Returns:
            Property: The property object if the user has permission.

        Raises:
            Http404: If the user doesn't have permission to access the property.
        """
        obj = super().get_object(queryset)
        if (
            obj.landlord.user != self.request.user
            and self.request.user.role != CustomUser.RoleChoices.ADMINISTRATOR
        ):
            raise Http404("Property not found")
        return obj


# ====== Building Views ======
class BuildingListView(LoginRequiredMixin, LandlordRequiredMixin, ListView):
    model = Building
    template_name = "building_list.html"
    context_object_name = "buildings"

    def get_queryset(self):
        return Building.objects.filter(landlord=self.request.user.landlord).order_by("name")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Modal form for adding buildings
        from .forms import BuildingForm
        ctx["building_form"] = BuildingForm()
        return ctx


class BuildingCreateView(LoginRequiredMixin, LandlordRequiredMixin, CreateView):
    model = Building
    form_class = BuildingForm
    template_name = "building_form.html"
    success_url = reverse_lazy("property_list")

    def form_valid(self, form):
        form.instance.landlord = self.request.user.landlord
        messages.success(self.request, "Building created successfully.")
        return super().form_valid(form)


class BuildingUpdateView(LoginRequiredMixin, LandlordRequiredMixin, UpdateView):
    model = Building
    form_class = BuildingForm
    template_name = "building_form.html"
    success_url = reverse_lazy("building_list")

    def get_queryset(self):
        return Building.objects.filter(landlord=self.request.user.landlord)


class BuildingDeleteView(LoginRequiredMixin, LandlordRequiredMixin, DeleteView):
    model = Building
    success_url = reverse_lazy("property_list")

    def get_queryset(self):
        return Building.objects.filter(landlord=self.request.user.landlord)

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Building deleted successfully.")
        return super().delete(request, *args, **kwargs)


# ====== Unit Views ======
class UnitListView(LoginRequiredMixin, LandlordRequiredMixin, ListView):
    model = Unit
    template_name = "unit_list.html"
    context_object_name = "units"

    def get_queryset(self):
        return (
            Unit.objects.filter(building__landlord=self.request.user.landlord)
            .select_related("building")
            .order_by("building__name", "number")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Modal forms for adding related objects (restrict choices to landlord scope)
        unit_form = UnitForm()
        unit_form.fields["building"].queryset = Building.objects.filter(landlord=self.request.user.landlord)

        equipment_form = EquipmentForm()
        equipment_form.fields["unit"].queryset = Unit.objects.filter(
            building__landlord=self.request.user.landlord
        )

        meter_form = MeterForm()
        meter_form.fields["unit"].queryset = Unit.objects.filter(
            building__landlord=self.request.user.landlord
        )

        ctx.update({
            "unit_form": unit_form,
            "equipment_form": equipment_form,
            "meter_form": meter_form,
        })
        return ctx


class UnitCreateView(LoginRequiredMixin, LandlordRequiredMixin, CreateView):
    model = Unit
    form_class = UnitForm
    template_name = "unit_form.html"
    success_url = reverse_lazy("unit_list")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["building"].queryset = Building.objects.filter(
            landlord=self.request.user.landlord
        )
        return form

    def get_initial(self):
        initial = super().get_initial()
        building_id = self.request.GET.get("building")
        if building_id:
            try:
                bld = Building.objects.get(id=building_id, landlord=self.request.user.landlord)
                initial["building"] = bld.id
            except Building.DoesNotExist:
                pass
        return initial

    def form_valid(self, form):
        # If a building is provided via query param and belongs to this landlord, bind it explicitly
        building_id = self.request.GET.get("building")
        if building_id:
            try:
                bld = Building.objects.get(id=building_id, landlord=self.request.user.landlord)
                form.instance.building = bld
            except Building.DoesNotExist:
                pass
        messages.success(self.request, "Unit created successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        # After creating a unit, go back to its building detail if available
        try:
            return reverse_lazy("building_detail", kwargs={"pk": self.object.building.pk})
        except Exception:
            return reverse_lazy("unit_list")


class UnitUpdateView(LoginRequiredMixin, LandlordRequiredMixin, UpdateView):
    model = Unit
    form_class = UnitForm
    template_name = "unit_form.html"
    success_url = reverse_lazy("unit_list")

    def get_queryset(self):
        return Unit.objects.filter(building__landlord=self.request.user.landlord)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["building"].queryset = Building.objects.filter(
            landlord=self.request.user.landlord
        )
        return form


class UnitDeleteView(LoginRequiredMixin, LandlordRequiredMixin, DeleteView):
    model = Unit
    success_url = reverse_lazy("unit_list")

    def get_queryset(self):
        return Unit.objects.filter(building__landlord=self.request.user.landlord)

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Unit deleted successfully.")
        return super().delete(request, *args, **kwargs)


# ====== Equipment Views ======
class EquipmentCreateView(LoginRequiredMixin, LandlordRequiredMixin, CreateView):
    model = Equipment
    form_class = EquipmentForm
    template_name = "equipment_form.html"
    success_url = reverse_lazy("unit_list")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["unit"].queryset = Unit.objects.filter(
            building__landlord=self.request.user.landlord
        )
        return form

    def get_initial(self):
        initial = super().get_initial()
        unit_id = self.request.GET.get("unit")
        if unit_id:
            try:
                unit = Unit.objects.get(id=unit_id, building__landlord=self.request.user.landlord)
                initial["unit"] = unit.id
            except Unit.DoesNotExist:
                pass
        return initial

    def get_success_url(self):
        try:
            return reverse_lazy("unit_detail", kwargs={"pk": self.object.unit.pk})
        except Exception:
            return reverse_lazy("unit_list")


class EquipmentUpdateView(LoginRequiredMixin, LandlordRequiredMixin, UpdateView):
    model = Equipment
    form_class = EquipmentForm
    template_name = "equipment_form.html"
    success_url = reverse_lazy("unit_list")

    def get_queryset(self):
        return Equipment.objects.filter(unit__building__landlord=self.request.user.landlord)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["unit"].queryset = Unit.objects.filter(
            building__landlord=self.request.user.landlord
        )
        return form


class EquipmentDeleteView(LoginRequiredMixin, LandlordRequiredMixin, DeleteView):
    model = Equipment
    success_url = reverse_lazy("unit_list")

    def get_queryset(self):
        return Equipment.objects.filter(unit__building__landlord=self.request.user.landlord)

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Equipment deleted successfully.")
        return super().delete(request, *args, **kwargs)


# ====== Meter Views ======
class MeterCreateView(LoginRequiredMixin, LandlordRequiredMixin, CreateView):
    model = Meter
    form_class = MeterForm
    template_name = "meter_form.html"
    success_url = reverse_lazy("unit_list")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["unit"].queryset = Unit.objects.filter(
            building__landlord=self.request.user.landlord
        )
        return form

    def get_initial(self):
        initial = super().get_initial()
        unit_id = self.request.GET.get("unit")
        if unit_id:
            try:
                unit = Unit.objects.get(id=unit_id, building__landlord=self.request.user.landlord)
                initial["unit"] = unit.id
            except Unit.DoesNotExist:
                pass
        return initial

    def get_success_url(self):
        try:
            return reverse_lazy("unit_detail", kwargs={"pk": self.object.unit.pk})
        except Exception:
            return reverse_lazy("unit_list")


class MeterUpdateView(LoginRequiredMixin, LandlordRequiredMixin, UpdateView):
    model = Meter
    form_class = MeterForm
    template_name = "meter_form.html"
    success_url = reverse_lazy("unit_list")

    def get_queryset(self):
        return Meter.objects.filter(unit__building__landlord=self.request.user.landlord)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["unit"].queryset = Unit.objects.filter(
            building__landlord=self.request.user.landlord
        )
        return form


class MeterDeleteView(LoginRequiredMixin, LandlordRequiredMixin, DeleteView):
    model = Meter
    success_url = reverse_lazy("unit_list")

    def get_queryset(self):
        return Meter.objects.filter(unit__building__landlord=self.request.user.landlord)

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Meter deleted successfully.")
        return super().delete(request, *args, **kwargs)



# ====== Hierarchical Detail Views ======
class BuildingDetailView(LoginRequiredMixin, LandlordRequiredMixin, ListView):
    """Show a single building with its units."""

    model = Unit
    template_name = "building_detail.html"
    context_object_name = "units"

    def get_queryset(self):
        # List units that belong to this building, scoped to landlord
        self.building = Building.objects.filter(
            landlord=self.request.user.landlord, id=self.kwargs["pk"]
        ).first()
        if not self.building:
            raise Http404("Building not found")
        return (
            Unit.objects.filter(building=self.building)
            .select_related("building")
            .order_by("number")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["building"] = self.building
        # Modal Unit form prefilled with this building
        from .forms import UnitForm, EquipmentForm, MeterForm
        unit_form = UnitForm(initial={"building": self.building.id})
        unit_form.fields["building"].queryset = Building.objects.filter(landlord=self.request.user.landlord)
        
        # Forms for adding equipment and meters (unit choices scoped to landlord)
        equipment_form = EquipmentForm()
        equipment_form.fields["unit"].queryset = Unit.objects.filter(building__landlord=self.request.user.landlord)
        meter_form = MeterForm()
        meter_form.fields["unit"].queryset = Unit.objects.filter(building__landlord=self.request.user.landlord)
        
        ctx["unit_form"] = unit_form
        ctx["equipment_form"] = equipment_form
        ctx["meter_form"] = meter_form
        return ctx


class UnitDetailView(LoginRequiredMixin, LandlordRequiredMixin, ListView):
    """Show a single unit with its equipment and meters."""

    model = Equipment
    template_name = "unit_detail.html"
    context_object_name = "equipment"

    def get_queryset(self):
        # Verify unit ownership and return its equipment
        self.unit = (
            Unit.objects.select_related("building")
            .filter(building__landlord=self.request.user.landlord, id=self.kwargs["pk"])  # noqa: E501
            .first()
        )
        if not self.unit:
            raise Http404("Unit not found")
        return Equipment.objects.filter(unit=self.unit).order_by("name")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["unit"] = self.unit
        ctx["meters"] = Meter.objects.filter(unit=self.unit).order_by("meter_type", "serial")
        # Modal forms for adds on unit page
        from .forms import EquipmentForm, MeterForm
        equipment_form = EquipmentForm(initial={"unit": self.unit.id})
        meter_form = MeterForm(initial={"unit": self.unit.id})
        # Restrict unit choices to landlord units
        equipment_form.fields["unit"].queryset = Unit.objects.filter(building__landlord=self.request.user.landlord)
        meter_form.fields["unit"].queryset = Unit.objects.filter(building__landlord=self.request.user.landlord)
        ctx["equipment_form"] = equipment_form
        ctx["meter_form"] = meter_form
        return ctx
