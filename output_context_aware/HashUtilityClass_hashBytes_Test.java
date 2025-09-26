package com.example.pdfcompare.util;

import com.example.pdfcompare.util.HashUtilityClass;
import java.lang.StringBuilder;
import java.math.BigInteger;
import java.security.MessageDigest;
import java.util.Arrays;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

public class HashUtilityClassTest {

@BeforeEach
public void setUp() {
}

@AfterEach
public void tearDown() {
}

@Test
public void testHashBytes_normalData_expectedMD5Hash() {
byte[] data = "test".getBytes();
String expectedHash = "098f6bcd4621d373cade4e832627b4f6";
String result = HashUtilityClass.hashBytes(data);
assertEquals(expectedHash, result);
}

}