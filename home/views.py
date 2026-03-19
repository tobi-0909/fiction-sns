from django.shortcuts import render
import markdown
import os


def index(request):
    return render(request, "home/index.html")


def tos_view(request):
    """利用規約ページを表示"""
    doc_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'docs', 'TOS.md')
    try:
        with open(doc_path, 'r', encoding='utf-8') as f:
            tos_md = f.read()
        tos_html = markdown.markdown(tos_md, extensions=['tables', 'toc'])
    except FileNotFoundError:
        tos_html = "<p>利用規約が見つかりません。</p>"
    
    return render(request, "tos.html", {"tos_content": tos_html})


def privacy_view(request):
    """プライバシーポリシーページを表示"""
    doc_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'docs', 'PRIVACY_POLICY.md')
    try:
        with open(doc_path, 'r', encoding='utf-8') as f:
            privacy_md = f.read()
        privacy_html = markdown.markdown(privacy_md, extensions=['tables', 'toc'])
    except FileNotFoundError:
        privacy_html = "<p>プライバシーポリシーが見つかりません。</p>"
    
    return render(request, "privacy.html", {"privacy_content": privacy_html})
