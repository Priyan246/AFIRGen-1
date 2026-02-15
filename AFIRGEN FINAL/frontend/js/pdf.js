/**
 * PDF Export Module
 * Handles PDF generation and export for FIR documents
 * Requires: jsPDF library (lib/jspdf.min.js)
 */

/**
 * Check if jsPDF is available
 * @returns {boolean}
 */
function isJsPDFAvailable() {
    return typeof window.jspdf !== 'undefined' && typeof window.jspdf.jsPDF !== 'undefined';
}

/**
 * Generate PDF from FIR data
 * @param {Object} firData - FIR data object
 * @param {Object} options - PDF generation options
 * @returns {Object} jsPDF instance or null
 */
function generatePDF(firData, options = {}) {
    if (!isJsPDFAvailable()) {
        console.error('jsPDF library not loaded. Please include jspdf.min.js');
        if (window.showToast) {
            window.showToast('PDF library not available', 'error');
        }
        return null;
    }

    try {
        const { jsPDF } = window.jspdf;
        
        // Create new PDF document (A4 portrait)
        const doc = new jsPDF({
            orientation: 'portrait',
            unit: 'mm',
            format: 'a4'
        });

        // PDF dimensions
        const pageWidth = doc.internal.pageSize.getWidth();
        const pageHeight = doc.internal.pageSize.getHeight();
        const margin = 20;
        const contentWidth = pageWidth - (2 * margin);
        let yPosition = margin;

        // Helper function to add text with word wrap
        const addText = (text, fontSize = 10, isBold = false) => {
            doc.setFontSize(fontSize);
            doc.setFont('helvetica', isBold ? 'bold' : 'normal');
            
            const lines = doc.splitTextToSize(text, contentWidth);
            
            // Check if we need a new page
            if (yPosition + (lines.length * fontSize * 0.35) > pageHeight - margin) {
                doc.addPage();
                yPosition = margin;
            }
            
            doc.text(lines, margin, yPosition);
            yPosition += lines.length * fontSize * 0.35 + 3;
        };

        // Helper function to add a line separator
        const addLine = () => {
            if (yPosition + 5 > pageHeight - margin) {
                doc.addPage();
                yPosition = margin;
            }
            doc.setDrawColor(200, 200, 200);
            doc.line(margin, yPosition, pageWidth - margin, yPosition);
            yPosition += 5;
        };

        // Header
        doc.setFillColor(240, 240, 240);
        doc.rect(0, 0, pageWidth, 40, 'F');
        
        doc.setFontSize(20);
        doc.setFont('helvetica', 'bold');
        doc.text('FIRST INFORMATION REPORT', pageWidth / 2, 15, { align: 'center' });
        
        doc.setFontSize(14);
        doc.setFont('helvetica', 'normal');
        doc.text(firData.number || 'FIR Number Not Available', pageWidth / 2, 25, { align: 'center' });
        
        yPosition = 50;

        // FIR Details Section
        addText('FIR DETAILS', 14, true);
        addLine();

        if (firData.number) {
            addText(`FIR Number: ${firData.number}`, 11, true);
        }

        if (firData.date) {
            const date = new Date(firData.date);
            addText(`Date: ${date.toLocaleDateString('en-IN', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric'
            })}`, 10);
            addText(`Time: ${date.toLocaleTimeString('en-IN', {
                hour: '2-digit',
                minute: '2-digit'
            })}`, 10);
        }

        if (firData.location || firData.policeStation) {
            addText(`Police Station: ${firData.policeStation || firData.location || 'Not specified'}`, 10);
        }

        yPosition += 5;

        // Complainant Information
        if (firData.complainant) {
            addText('COMPLAINANT INFORMATION', 12, true);
            addLine();
            addText(firData.complainant, 10);
            yPosition += 5;
        }

        // Complaint Details
        if (firData.description || firData.content || firData.fir_content) {
            addText('COMPLAINT DETAILS', 12, true);
            addLine();
            const content = firData.description || firData.content || firData.fir_content;
            addText(content, 10);
            yPosition += 5;
        }

        // Status Information
        if (firData.status) {
            addText('STATUS INFORMATION', 12, true);
            addLine();
            addText(`Status: ${capitalizeFirst(firData.status)}`, 10);
            
            if (firData.officer) {
                addText(`Assigned Officer: ${firData.officer}`, 10);
            }
            
            yPosition += 5;
        }

        // Footer on last page
        const pageCount = doc.internal.getNumberOfPages();
        for (let i = 1; i <= pageCount; i++) {
            doc.setPage(i);
            doc.setFontSize(8);
            doc.setFont('helvetica', 'normal');
            doc.setTextColor(128, 128, 128);
            
            // Page number
            doc.text(
                `Page ${i} of ${pageCount}`,
                pageWidth / 2,
                pageHeight - 10,
                { align: 'center' }
            );
            
            // Generated timestamp
            const timestamp = new Date().toLocaleString('en-IN');
            doc.text(
                `Generated: ${timestamp}`,
                margin,
                pageHeight - 10
            );
            
            // Watermark
            doc.text(
                'AFIRGen - AI-powered FIR Management',
                pageWidth - margin,
                pageHeight - 10,
                { align: 'right' }
            );
        }

        return doc;
    } catch (error) {
        console.error('Error generating PDF:', error);
        if (window.showToast) {
            window.showToast('Failed to generate PDF', 'error');
        }
        return null;
    }
}

/**
 * Download PDF to user's device
 * @param {Object} pdf - jsPDF instance
 * @param {string} filename - Filename for download
 */
function downloadPDF(pdf, filename = 'FIR-Report.pdf') {
    if (!pdf) {
        console.error('No PDF instance provided');
        return;
    }

    try {
        // Sanitize filename
        const sanitizedFilename = filename.replace(/[^a-z0-9.-]/gi, '_');
        
        // Download the PDF
        pdf.save(sanitizedFilename);
        
        if (window.showToast) {
            window.showToast('PDF downloaded successfully', 'success', 3000);
        }
    } catch (error) {
        console.error('Error downloading PDF:', error);
        if (window.showToast) {
            window.showToast('Failed to download PDF', 'error');
        }
    }
}

/**
 * Print PDF directly
 * @param {Object} pdf - jsPDF instance
 */
function printPDF(pdf) {
    if (!pdf) {
        console.error('No PDF instance provided');
        return;
    }

    try {
        // Open PDF in new window for printing
        const pdfBlob = pdf.output('blob');
        const pdfUrl = URL.createObjectURL(pdfBlob);
        
        const printWindow = window.open(pdfUrl, '_blank');
        
        if (printWindow) {
            printWindow.onload = () => {
                printWindow.print();
                // Clean up URL after a delay
                setTimeout(() => {
                    URL.revokeObjectURL(pdfUrl);
                }, 1000);
            };
        } else {
            // Fallback: download if popup blocked
            console.warn('Print window blocked, falling back to download');
            downloadPDF(pdf, 'FIR-Report-Print.pdf');
        }
    } catch (error) {
        console.error('Error printing PDF:', error);
        if (window.showToast) {
            window.showToast('Failed to print PDF', 'error');
        }
    }
}

/**
 * Export FIR as PDF
 * @param {Object} firData - FIR data object
 * @param {Object} options - Export options
 */
function exportFIRAsPDF(firData, options = {}) {
    const {
        download = true,
        print = false,
        filename = null
    } = options;

    // Generate PDF
    const pdf = generatePDF(firData, options);
    
    if (!pdf) {
        return;
    }

    // Generate filename if not provided
    const defaultFilename = firData.number 
        ? `FIR-${firData.number.replace(/\//g, '-')}.pdf`
        : `FIR-${Date.now()}.pdf`;
    
    const finalFilename = filename || defaultFilename;

    // Download or print
    if (print) {
        printPDF(pdf);
    } else if (download) {
        downloadPDF(pdf, finalFilename);
    }

    return pdf;
}

// Utility function
function capitalizeFirst(str) {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1);
}

// Export functions
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        generatePDF,
        downloadPDF,
        printPDF,
        exportFIRAsPDF,
        isJsPDFAvailable
    };
}

// Make functions available globally
if (typeof window !== 'undefined') {
    window.PDFExport = {
        generate: generatePDF,
        download: downloadPDF,
        print: printPDF,
        export: exportFIRAsPDF,
        isAvailable: isJsPDFAvailable
    };
}
