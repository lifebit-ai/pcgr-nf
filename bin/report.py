#!/usr/bin/env python

import os
import sys
import shutil
import html
import base64

html_template = """
<!DOCTYPE html>
<html lang="en">
    <style>
        {0}
    </style>
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>PCGR Report</title>
        <link rel="stylesheet" href="style.css">
    </head>
    <body style="background-color: #FFFFFF">
        <div id="root">
            <h1>PCGR Report Overview</h1>
            <img src="data:image/png;base64,{1}" width=100 style="position:absolute;top:4px;bottom:4px;right:4px;" />
        </div>
        <div id="TOC">
            <p class="toc_title">Contents</p>
            <ul class="toc_list">
            {2}
        </ul>
        </div>
        {3}
    </body>
</html>
"""

def __main__():
    css_style = sys.argv[1]
    lifebit_logo = sys.argv[2]
    pcgr_reports = sys.argv[3:]
    print(pcgr_reports)

    if len(pcgr_reports) == 1:
        shutil.copyfile(pcgr_reports[0], "multiqc_report.html", follow_symlinks=True)
    else:

        style_css = open(css_style).read()
        logo_uri = base64.b64encode(open(lifebit_logo, 'rb').read()).decode('utf-8')

        toc_contents = ""
        iframe_div_contents = ""

        for report in pcgr_reports:
            sample_id = report.replace("_pcgr.html","")
            report_content = open(report).read().replace('\n', '')
            toc_contents += """
                            <li><a href="#{0}">{0}</a>
                            """.format(sample_id)
            iframe_div_contents += """
                                    <div>
                                        <h2 id="{0}">{0}</h2>
                                        <p align="center">
                                            <iframe seamless sandbox srcdoc="{1}" name="targetframe" allowTransparency="true" scrolling="yes" frameborder="0" width="700px" height="500"></iframe>
                                        </p>
                                    </div>
                                    """.format(sample_id, html.escape(report_content, quote=True))

        with open("multiqc_report.html", "w") as fh:
            fh.write(html_template.format(style_css, logo_uri, toc_contents, iframe_div_contents))

if __name__=="__main__": __main__()