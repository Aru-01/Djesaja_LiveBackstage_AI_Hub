from rest_framework import serializers


class AdminDashboardSerializer(serializers.Serializer):
    total_creators = serializers.IntegerField()
    total_managers = serializers.IntegerField()
    scrape_today = serializers.IntegerField()
    total_diamond_achieve = serializers.IntegerField()
    total_coin = serializers.FloatField()
    total_hour = serializers.FloatField()


class ManagerDashboardSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    my_creators = serializers.IntegerField()
    rank = serializers.IntegerField()
    total_coin = serializers.FloatField()
    total_hour = serializers.FloatField()
    total_diamond = serializers.IntegerField()


class CreatorDashboardSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    manager_id = serializers.IntegerField()
    manager_username = serializers.CharField()
    total_coin = serializers.FloatField()
    total_hour = serializers.FloatField()
    total_diamond = serializers.IntegerField()
    rank = serializers.IntegerField()
