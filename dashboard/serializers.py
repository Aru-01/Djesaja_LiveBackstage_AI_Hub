from rest_framework import serializers


class AdminDashboardSerializer(serializers.Serializer):
    total_creators = serializers.IntegerField()
    total_managers = serializers.IntegerField()
    scrape_today = serializers.IntegerField()
    total_diamond_achieve = serializers.IntegerField()
    last_3_months = serializers.DictField()
    target_diamonds = serializers.IntegerField()
    total_coin = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_hour = serializers.DecimalField(max_digits=10, decimal_places=2)


class ManagerDashboardSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    profile_image = serializers.SerializerMethodField()
    my_creators = serializers.IntegerField()
    rank = serializers.IntegerField()
    at_risk = serializers.IntegerField()
    excellent = serializers.IntegerField()
    last_3_months = serializers.DictField()
    total_coin = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_hour = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_diamond = serializers.IntegerField()
    target_diamonds = serializers.IntegerField()

    def get_profile_image(self, obj):
        request = self.context.get("request")
        image = obj.get("profile_image")

        if image and request:
            return request.build_absolute_uri(image)

        return None


class CreatorDashboardSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    profile_image = serializers.SerializerMethodField()
    manager_id = serializers.IntegerField()
    manager_username = serializers.CharField()
    total_coin = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_hour = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_diamond = serializers.IntegerField()
    last_3_months = serializers.DictField()
    target_diamonds = serializers.IntegerField()
    rank = serializers.IntegerField()

    def get_profile_image(self, obj):
        request = self.context.get("request")
        image = obj.get("profile_image")

        if image and request:
            return request.build_absolute_uri(image)

        return None
