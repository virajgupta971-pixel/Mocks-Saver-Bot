import sys
import re
from bs4 import BeautifulSoup

def inject_section_locking_logic(html_content):
    """
    Oliveboard HTML Interface me Section Locking aur Sequential Navigation
    ko enforce karne ke liye JavaScript logic inject karta hai.
    """
    locking_script = """
    <!-- Custom Section Locking & Sequential Progression Script -->
    <script type="text/javascript">
    (function() {
        // Track the index of the highest unlocked section (0 = First Section)
        window.currentUnlockedSection = 0;

        // Wait until DOM is completely loaded
        document.addEventListener("DOMContentLoaded", function() {
            
            // 1. Override shiftSection to block unauthorized navigation
            if (typeof window.shiftSection === 'function') {
                var originalShiftSection = window.shiftSection;
                window.shiftSection = function(sid) {
                    // Check if user is trying to jump to a locked section
                    if (sid > window.currentUnlockedSection) {
                        alert("🔒 Section Locked! Aapko pehle current section complete karna hoga.");
                        return false;
                    }
                    // Call original shiftSection if section is unlocked
                    return originalShiftSection.apply(this, arguments);
                };
            }

            // 2. Override sendData / Section Submit to unlock the next section
            if (typeof window.sendData === 'function') {
                var originalSendData = window.sendData;
                window.sendData = function() {
                    // Unlock next section index if available
                    if (typeof secList !== 'undefined' && Array.isArray(secList)) {
                        if (window.currentUnlockedSection < secList.length - 1) {
                            window.currentUnlockedSection++;
                            console.log("Next section unlocked. Current unlocked index: " + window.currentUnlockedSection);
                        }
                    } else {
                        window.currentUnlockedSection++;
                    }

                    // Execute original sendData / submit execution
                    return originalSendData.apply(this, arguments);
                };
            }

            // 3. Optional: Visual indicator update for locked section tabs
            function updateSectionTabStyles() {
                if (typeof secList !== 'undefined' && Array.isArray(secList)) {
                    secList.forEach(function(sec, index) {
                        var tabElem = document.getElementById("sec_tab_" + index) || document.getElementById("section_" + index);
                        if (tabElem) {
                            if (index > window.currentUnlockedSection) {
                                tabElem.style.opacity = "0.5";
                                tabElem.style.cursor = "not-allowed";
                                tabElem.title = "Section Locked";
                            } else {
                                tabElem.style.opacity = "1";
                                tabElem.style.cursor = "pointer";
                                tabElem.title = "";
                            }
                        }
                    });
                }
            }

            // Run visual update periodically or on click
            setInterval(updateSectionTabStyles, 1000);
        });
    })();
    </script>
    """

    # HTML ke </body> tag ke theek pehle script inject karein
    if "</body>" in html_content:
        modified_html = html_content.replace("</body>", f"{locking_script}\n</body>")
    else:
        modified_html = html_content + locking_script

    return modified_html


def process_html_file(input_path, output_path):
    """
    Input HTML file ko read karta hai, logic inject karta hai, aur output file save karta hai.
    """
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        print(f"[+] Processing file: {input_path}")
        
        # Inject the custom lock logic
        updated_html = inject_section_locking_logic(html_content)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(updated_html)

        print(f"[✓] File successfully updated and saved to: {output_path}")

    except Exception as e:
        print(f"[X] Error processing file: {str(e)}")


if __name__ == "__main__":
    # Standard Usage: python main.py <input_file.html> <output_file.html>
    if len(sys.argv) >= 3:
        input_file = sys.argv[1]
        output_file = sys.argv[2]
    else:
        # Default fallback names agar terminal arguments na diye jayein
        input_file = "test_interface.html"
        output_file = "test_interface_locked.html"

    process_html_file(input_file, output_file)
