package com.example.pdfcompare.util;

import com.example.pdfcompare.util.PDFHighlighter;
import com.itextpdf.text.BaseColor;
import com.itextpdf.text.Rectangle;
import com.itextpdf.text.pdf.PdfContentByte;
import com.itextpdf.text.pdf.PdfGState; // Added missing import
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import static org.mockito.Mockito.*;
import static org.junit.jupiter.api.Assertions.*;

@ExtendWith(MockitoExtension.class)
public class PDFHighlighterTest {

@Mock
private PdfContentByte mockPdfContentByte;
@Mock
private Rectangle mockRectangle;
@Mock
private BaseColor mockBaseColor;

private PDFHighlighter pdfHighlighter;

@BeforeEach
public void setUp() {
pdfHighlighter = new PDFHighlighter();
}

@AfterEach
public void tearDown() {
pdfHighlighter = null;
}

@Test
public void testHighlightEntirePage_NormalCase_ExpectStateSavedAndRestored() {
pdfHighlighter.highlightEntirePage(mockPdfContentByte, mockRectangle, mockBaseColor, 10f);
verify(mockPdfContentByte, times(1)).saveState();
verify(mockPdfContentByte, times(1)).restoreState();
}

@Test
public void testHighlightEntirePage_NullPdfContentByte_ExpectNullPointerException() {
assertThrows(NullPointerException.class, () -> pdfHighlighter.highlightEntirePage(null, mockRectangle, mockBaseColor, 10f));
}

@Test
public void testHighlightEntirePage_NullRectangle_ExpectNullPointerException() {
assertThrows(NullPointerException.class, () -> pdfHighlighter.highlightEntirePage(mockPdfContentByte, null, mockBaseColor, 10f));
}

@Test
public void testHighlightEntirePage_NullBaseColor_ExpectNullPointerException() {
doThrow(new NullPointerException("Color is null")).when(mockPdfContentByte).setColorFill(null);
assertThrows(NullPointerException.class, () -> pdfHighlighter.highlightEntirePage(mockPdfContentByte, mockRectangle, null, 10f));
}

@Test
public void testHighlightEntirePage_NullXOffset_ExpectNullPointerException() {
assertThrows(NullPointerException.class, () -> pdfHighlighter.highlightEntirePage(mockPdfContentByte, mockRectangle, mockBaseColor, (Float) null));
}

@Test
public void testHighlightEntirePage_ValidateRectangleCoordinates_ExpectCorrectValues() {
when(mockRectangle.getLeft()).thenReturn(100f);
when(mockRectangle.getBottom()).thenReturn(200f);
when(mockRectangle.getWidth()).thenReturn(300f);
when(mockRectangle.getHeight()).thenReturn(400f);
pdfHighlighter.highlightEntirePage(mockPdfContentByte, mockRectangle, mockBaseColor, 10f);
verify(mockPdfContentByte, times(1)).rectangle(110f, 200f, 300f, 400f);
}

@Test
public void testHighlightEntirePage_ValidateGStateAndColorSet_ExpectCorrectCalls() {
pdfHighlighter.highlightEntirePage(mockPdfContentByte, mockRectangle, mockBaseColor, 10f);
verify(mockPdfContentByte, times(1)).setGState(any(PdfGState.class));
verify(mockPdfContentByte, times(1)).setColorFill(mockBaseColor);
}

@Test
public void testHighlightEntirePage_ValidateFillCall_ExpectCorrectCall() {
pdfHighlighter.highlightEntirePage(mockPdfContentByte, mockRectangle, mockBaseColor, 10f);
verify(mockPdfContentByte, times(1)).fill();
}
}