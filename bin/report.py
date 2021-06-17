#!/usr/bin/env python

import os
import sys
import shutil

html_template_top = """
<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>PCGR Report</title>
        <script type="text/javascript">
            function goToNewPage()
            {
                var url = document.getElementById('list').value;
                if(url != 'none') {
                    window.location = url;
                }
            }
        </script>
    </head>
    <body style="background-color: #FFFFFF">
        <div id="root">
            <form>
            <select name="list" id="list" accesskey="target">
                <option value='none' selected>Choose a report</option>
"""
html_template_bottom = """
            </select>
            <input type=button value="Go" onclick="goToNewPage()" />
            </form>
        </div>
    </body>
</html>
"""
def __main__():
    
    pcgr_reports = sys.argv[1:]
    print(pcgr_reports)

    if len(pcgr_reports) == 1:
        shutil.copyfile(pcgr_reports[0], "multiqc_report.html", follow_symlinks=True)
    else:
        with open("multiqc_report.html", "w") as fh:
            fh.write(html_template_top)
            for report in pcgr_reports:
                str_option = "                <option value='{0}'>{0}</option>\n".format(report)
                fh.write(str_option)
            fh.write(html_template_bottom)


if __name__=="__main__": __main__()