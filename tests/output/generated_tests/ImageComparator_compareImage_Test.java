package com.example.pdfcompare.util;

import com.example.pdfcompare.util.ImageComparator;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import static org.junit.jupiter.api.Assertions.assertDoesNotThrow;
import static org.junit.jupiter.api.Assertions.assertThrows;

@ExtendWith(MockitoExtension.class)
public class ImageComparatorTest {

@InjectMocks
private ImageComparator imageComparator;

@Mock
private com.itextpdf.text.pdf.PdfContentByte pdfContentByteMock;

@BeforeEach
public void setUp() {
// Setup code if needed
}

@AfterEach
public void tearDown() {
// Teardown code if needed
}

@Test
public void testCompareImages_NormalCase_Success() {
assertDoesNotThrow(() -> imageComparator.compareImages(pdfContentByteMock, null, null, 0, false));
}

@Test
public void testCompareImages_NullInput_ThrowsException() {
assertThrows(IllegalArgumentException.class, () -> imageComparator.compareImages(null, null, null, 0, false));
}

@Test
public void testCompareImages_ResourceNotFound_ThrowsException() {
assertThrows(RuntimeException.class, () -> imageComparator.compareImages(pdfContentByteMock, null, null, 0, false));
}

@Test
public void testCompareImages_InvalidParameter_ThrowsException() {
assertThrows(IllegalArgumentException.class, () -> imageComparator.compareImages(pdfContentByteMock, null, null, 0, false));
}
}