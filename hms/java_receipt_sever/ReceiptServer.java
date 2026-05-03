import com.sun.net.httpserver.HttpServer;
import com.sun.net.httpserver.HttpHandler;
import com.sun.net.httpserver.HttpExchange;
import com.google.gson.Gson;
import java.io.IOException;

import java.io.*;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import java.util.stream.Collectors;

public class ReceiptServer {
    public static void main(String[] args) throws IOException {
        HttpServer server = HttpServer.create(new InetSocketAddress(8080), 0);
        server.createContext("/receipt", new ReceiptHandler());
        server.setExecutor(null);
        server.start();
        System.out.println("Receipt server started on port 8080");
    }

    static class ReceiptHandler implements HttpHandler {
        private final Gson gson = new Gson();

        @Override
        public void handle(HttpExchange exchange) throws IOException {
            if ("POST".equals(exchange.getRequestMethod())) {
                // Read request body
                String body = new BufferedReader(
                    new InputStreamReader(exchange.getRequestBody(), StandardCharsets.UTF_8))
                    .lines()
                    .collect(Collectors.joining("\n"));

                // Parse JSON
                ReceiptRequest request = gson.fromJson(body, ReceiptRequest.class);

                // Compute tax and total
                double tax = request.totalAmount * (request.taxRate / 100);
                double grandTotal = request.totalAmount + tax;

                // Generate receipt ID
                String receiptId = UUID.randomUUID().toString();

                // Build response
                Map<String, Object> response = new HashMap<>();
                response.put("receiptId", receiptId);
                response.put("subtotal", request.totalAmount);
                response.put("tax", tax);
                response.put("total", grandTotal);
                response.put("pdfUrl", "/receipts/" + receiptId + ".pdf");

                String jsonResponse = gson.toJson(response);
                exchange.getResponseHeaders().set("Content-Type", "application/json");
                exchange.sendResponseHeaders(200, jsonResponse.getBytes().length);
                OutputStream os = exchange.getResponseBody();
                os.write(jsonResponse.getBytes());
                os.close();
            } else {
                exchange.sendResponseHeaders(405, -1);
            }
        }
    }

    static class ReceiptRequest {
        int bookingId;
        String roomType;
        int nights;
        double basePrice;
        double totalAmount;
        double taxRate;
    }
}