import com.itextpdf.text.*;
import com.itextpdf.text.pdf.PdfWriter;
import java.io.FileOutputStream;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

public class ReceiptService {
    public static Map<String, Object> generateReceipt(ReceiptServer.ReceiptRequest request) {
        double tax = request.totalAmount * (request.taxRate / 100);
        double grandTotal = request.totalAmount + tax;
        String receiptId = UUID.randomUUID().toString();

        // Generate PDF
        String filePath = "receipts/" + receiptId + ".pdf";
        try {
            Document document = new Document();
            PdfWriter.getInstance(document, new FileOutputStream(filePath));
            document.open();
            document.add(new Paragraph("HOTEL RECEIPT"));
            document.add(new Paragraph("Booking ID: " + request.bookingId));
            document.add(new Paragraph("Room Type: " + request.roomType));
            document.add(new Paragraph("Nights: " + request.nights));
            document.add(new Paragraph("Subtotal: $" + request.totalAmount));
            document.add(new Paragraph("Tax (" + request.taxRate + "%): $" + tax));
            document.add(new Paragraph("Total: $" + grandTotal));
            document.add(new Paragraph("Date: " + LocalDateTime.now().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME)));
            document.close();
        } catch (Exception e) {
            e.printStackTrace();
        }

        Map<String, Object> response = new HashMap<>();
        response.put("receiptId", receiptId);
        response.put("subtotal", request.totalAmount);
        response.put("tax", tax);
        response.put("total", grandTotal);
        response.put("pdfUrl", "/receipts/" + receiptId + ".pdf");
        return response;
    }
}