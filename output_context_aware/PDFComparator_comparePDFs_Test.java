package com.example.pdfcompare.util;

import com.example.pdfcompare.util.PDFComparator;
import com.example.pdfcompare.util.PDFPageComparator;
import com.itextpdf.text.Document;
import com.itextpdf.text.Rectangle;
import com.itextpdf.text.pdf.PdfReader;
import com.itextpdf.text.pdf.PdfWriter;
import com.itextpdf.text.pdf.PdfContentByte;
import com.itextpdf.text.pdf.PdfImportedPage;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.io.IOException;
import com.itextpdf.text.DocumentException;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import static org.mockito.Mockito.*;
import static org.junit.jupiter.api.Assertions.*;

@ExtendWith(MockitoExtension.class)
public class PDFComparatorTest {

@Mock
private PDFPageComparator pageComparator;

@InjectMocks
private PDFComparator pdfComparator;

private InputStream pdf1InputStream;
private InputStream pdf2InputStream;
private OutputStream outputStream;
private ByteArrayOutputStream outputStreamMock;

@BeforeEach
public void setUp() throws Exception {
pdf1InputStream = new ByteArrayInputStream("PDF1 content".getBytes());
pdf2InputStream = new ByteArrayInputStream("PDF2 content".getBytes());
outputStreamMock = new ByteArrayOutputStream();
outputStream = outputStreamMock;
}

@AfterEach
public void tearDown() throws Exception {
outputStreamMock.close();
}
}