// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract CertificateRegistry {
    struct Certificate {
        string refugeeName;
        string countryName;
        string dateOfBirth;
        string addres;
        string gender;
        string certificateId;
        string issueDate;
        string validUntil;
        address generatedBy;
    }

    mapping(address => Certificate) public certificates;
    mapping(string => address) public certificateIds;

    function issueCertificate(
        address recipient,
        string memory refugeeName,
        string memory countryName,
        string memory dateOfBirth,
        string memory addres,
        string memory gender,
        string memory certificateId,
        string memory issueDate,
        string memory validUntil,
        address generatedBy
    ) public {
        require(bytes(certificates[recipient].certificateId).length == 0, "Certificate already issued");
        require(certificateIds[certificateId] == address(0), "Certificate ID already exists");

        Certificate memory newCertificate = Certificate({
            refugeeName: refugeeName,
            countryName: countryName,
            dateOfBirth: dateOfBirth,
            addres: addres,
            gender: gender,
            certificateId: certificateId,
            issueDate: issueDate,
            validUntil: validUntil,
            generatedBy: generatedBy
        });

        certificates[recipient] = newCertificate;
        certificateIds[certificateId] = recipient;
    }

    function verifyCertificateById(string memory certificateId) public view returns (
        string memory refugeeName,
        string memory countryName,
        string memory dateOfBirth,
        string memory addres,
        string memory gender,
        string memory certificateId_,
        string memory issueDate,
        string memory validUntil,
        address generatedBy
    ) {
        address recipient = certificateIds[certificateId];
        require(recipient != address(0), "Certificate not found");
        
        Certificate storage cert = certificates[recipient];
        return (
            cert.refugeeName,
            cert.countryName,
            cert.dateOfBirth,
            cert.addres,
            cert.gender,
            cert.certificateId,
            cert.issueDate,
            cert.validUntil,
            cert.generatedBy
        );
    }

    function verifyCertificateByAddress(address recipient) public view returns (
        string memory refugeeName,
        string memory countryName,
        string memory dateOfBirth,
        string memory addres,
        string memory gender,
        string memory certificateId_,
        string memory issueDate,
        string memory validUntil,
        address generatedBy
    ) {
        Certificate storage cert = certificates[recipient];
        require(bytes(cert.certificateId).length != 0, "Certificate not found");
        
        return (
            cert.refugeeName,
            cert.countryName,
            cert.dateOfBirth,
            cert.addres,
            cert.gender,
            cert.certificateId,
            cert.issueDate,
            cert.validUntil,
            cert.generatedBy
        );
    }
}
