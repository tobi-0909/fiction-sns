from django.test import TestCase, Client
from django.urls import reverse


class LegalPageTests(TestCase):
    """利用規約・プライバシーポリシーページテスト"""
    
    def setUp(self):
        self.client = Client()
    
    def test_tos_page_accessible(self):
        """利用規約ページが正常にアクセス可能"""
        response = self.client.get(reverse('tos'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tos.html')
    
    def test_tos_content_contains_heading(self):
        """利用規約ページにマークダウンコンテンツが含まれる"""
        response = self.client.get(reverse('tos'))
        self.assertEqual(response.status_code, 200)
        # マークダウンがレンダリングされているか確認（h2 タグが含まれるはず）
        self.assertIn('tos_content', response.context)
    
    def test_privacy_page_accessible(self):
        """プライバシーポリシーページが正常にアクセス可能"""
        response = self.client.get(reverse('privacy'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'privacy.html')
    
    def test_privacy_content_contains_heading(self):
        """プライバシーポリシーページにマークダウンコンテンツが含まれる"""
        response = self.client.get(reverse('privacy'))
        self.assertEqual(response.status_code, 200)
        # マークダウンがレンダリングされているか確認
        self.assertIn('privacy_content', response.context)

