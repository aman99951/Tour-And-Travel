from rest_framework import serializers
from .models import Inquiry, UserProfile, Tour, Price, TourDetail, TourHotel, TourCity, Tourvisa


class PriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Price
        fields = [
            "adult_price",
            "twin_sharing_price",
            "extra_adult_price",
            "infant_price",
            "child_price",
            "no_of_pax",
            "validity_date_from",
            "validity_date_to",
            "active",
        ]


class TourDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = TourDetail
        fields = [
            "itinerary",
            "includes",
            "excludes",
            "cancellation_policy",
            "notes",
        ]


class TourHotelSerializer(serializers.ModelSerializer):
    destination_name = serializers.CharField(
        source="destination.name", read_only=True)
    city_name = serializers.CharField(source="city.name", read_only=True)

    class Meta:
        model = TourHotel
        fields = [
            "hotel_name",
            "destination_name",
            "city_name",
        ]


class InquirySerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.username", read_only=True)
    user_profile = serializers.SerializerMethodField()
    tour_name = serializers.CharField(
        source="tour.short_description", read_only=True)
    tour_code = serializers.CharField(source="tour.code", read_only=True)
    tour_type = serializers.CharField(
        source="tour.tour_type.name", read_only=True)
    tour_category = serializers.CharField(
        source="tour.category.name", read_only=True)
    number_of_nights = serializers.IntegerField(
        source="tour.number_of_nights", read_only=True)
    number_of_days = serializers.IntegerField(
        source="tour.number_of_days", read_only=True)
    departure_city = serializers.CharField(
        source="tour.departure_city", read_only=True)
    feature = serializers.BooleanField(source="tour.feature", read_only=True)
    new_arrival = serializers.BooleanField(
        source="tour.new_arrival", read_only=True)
    clearance_sale = serializers.BooleanField(
        source="tour.clearance_sale", read_only=True)
    active = serializers.BooleanField(source="tour.active", read_only=True)
    city_name = serializers.CharField(source="city.name", read_only=True)
    prices = PriceSerializer(source="tour.prices", many=True, read_only=True)
    tour_details = serializers.SerializerMethodField()
    tour_hotels = TourHotelSerializer(
        source="tour.tour_hotels", many=True, read_only=True)

    def get_user_profile(self, obj):
        try:
            profile = UserProfile.objects.get(email=obj.user.username)
            return {
                "email": profile.email,
                "mobile_number": profile.mobile_number,
                "first_name": profile.first_name,
                "last_name": profile.last_name,
                "address": profile.address,
                "city": profile.city,
                "country": profile.country,
            }
        except UserProfile.DoesNotExist:
            return None

    def get_tour_details(self, obj):
        try:
            details = TourDetail.objects.get(tour=obj.tour)
            return TourDetailSerializer(details).data
        except TourDetail.DoesNotExist:
            return None

    class Meta:
        model = Inquiry
        fields = [
            "id",
            "user",
            "user_name",
            "user_profile",
            "tour_name",
            "tour_code",
            "tour_type",
            "tour_category",
            "number_of_nights",
            "number_of_days",
            "departure_city",
            "feature",
            "new_arrival",
            "clearance_sale",
            "active",
            "city_name",
            "from_date",
            "to_date",
            "created_at",
            "message",
            "prices",
            "tour_details",
            "tour_hotels",
        ]


class PriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Price
        fields = [
            "adult_price",
            "twin_sharing_price",
            "extra_adult_price",
            "infant_price",
            "child_price",
            "no_of_pax",
            "validity_date_from",
            "validity_date_to",
            "active",
        ]


class TourDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = TourDetail
        fields = [
            "itinerary",
            "includes",
            "excludes",
            "cancellation_policy",
            "notes",
        ]


class TourHotelSerializer(serializers.ModelSerializer):
    destination_name = serializers.CharField(
        source="destination.name", read_only=True)
    city_name = serializers.CharField(source="city.name", read_only=True)

    class Meta:
        model = TourHotel
        fields = [
            "hotel_name",
            "destination_name",
            "city_name",
        ]


class TourCitySerializer(serializers.ModelSerializer):
    country_name = serializers.CharField(source="country.name", read_only=True)
    state_name = serializers.CharField(source="state.name", read_only=True)

    class Meta:
        model = TourCity
        fields = [
            "country_name",
            "state_name",
            "num_of_days",
            "num_of_nights",
        ]


class TourVisaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tourvisa
        fields = [
            "name_of_country",
        ]


class TourSerializer(serializers.ModelSerializer):
    tour_type = serializers.CharField(source="tour_type.name", read_only=True)
    tour_category = serializers.CharField(
        source="category.name", read_only=True)
    number_of_nights = serializers.IntegerField(read_only=True)
    number_of_days = serializers.IntegerField(read_only=True)
    departure_city = serializers.CharField(read_only=True)
    feature = serializers.BooleanField(read_only=True)
    new_arrival = serializers.BooleanField(read_only=True)
    clearance_sale = serializers.BooleanField(read_only=True)
    active = serializers.BooleanField(read_only=True)
    prices = PriceSerializer(many=True, read_only=True)
    tour_details = serializers.SerializerMethodField()
    tour_hotels = TourHotelSerializer(
        many=True, read_only=True)
    cities = TourCitySerializer(many=True, read_only=True)
    Visa = TourVisaSerializer(many=True, read_only=True)

    def get_tour_details(self, obj):
        try:
            details = TourDetail.objects.get(tour=obj)
            return TourDetailSerializer(details).data
        except TourDetail.DoesNotExist:
            return None

    class Meta:
        model = Tour
        fields = [
            "id",
            "code",
            "tour_type",
            "tour_category",
            "short_description",
            "long_description",
            "number_of_nights",
            "number_of_days",
            "currency",
            "departure_city",
            "feature",
            "new_arrival",
            "clearance_sale",
            "active",
            "prices",
            "tour_details",
            "tour_hotels",
            "cities",
            "Visa",
        ]
